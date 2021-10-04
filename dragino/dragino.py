#!/usr/bin/env python3
"""
Basic interface for dragino LoRa/GPS HAT
Copyright (C) 2018 Philip Basford

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from random import randrange
from datetime import datetime, timedelta
import logging
import os.path
from configobj import ConfigObj
from serial import Serial
import pynmea2
from .SX127x.LoRa import LoRa, MODE
from .SX127x.board_config import BOARD
from .LoRaWAN import new as lorawan_msg
from .LoRaWAN import MalformedPacketException
from .LoRaWAN.MHDR import MHDR
from .FrequncyPlan import LORA_FREQS, JOIN_FREQS


DEFAULT_LOG_LEVEL = logging.WARN #Change after finishing development
DEFAULT_RETRIES = 3 # How many attempts to send the message

AUTH_ABP = "ABP"
AUTH_OTAA = "OTAA"

class Dragino(LoRa):
    """
        Class to provide an interface to the dragino LoRa/GPS HAT
    """
    def __init__(
            self, config_filename, freqs=LORA_FREQS,
            logging_level=DEFAULT_LOG_LEVEL,
            lora_retries=DEFAULT_RETRIES):
        """
            Create the class to interface with the board
        """
        self.logger = logging.getLogger("Dragino")
        self.logger.setLevel(logging_level)
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
        BOARD.setup()
        super(Dragino, self).__init__(logging_level < logging.INFO)
        self.freqs = freqs
        #Set all auth method tockens to None as not sure what auth method we'll use
        self.device_addr = None
        self.network_key = None
        self.apps_key = None
        self.appkey = None
        self.appeui = None
        self.deveui = None
        self.transmitting = False
        self.config = DraginoConfig(config_filename, logging_level)
        self.lora_retries = lora_retries
        self._read_frame_count()
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([1, 0, 0, 0, 0, 0])
        self.set_pa_config(pa_select=1)
        self.set_spreading_factor(self.config.spreading_factor)
        self.set_pa_config(
            max_power=self.config.max_power,
            output_power=self.config.output_power)
        self.set_sync_word(self.config.sync_word)
        self.set_rx_crc(self.config.rx_crc)
        if self.config.auth == AUTH_ABP:
            self.device_addr = self.config.devaddr
            self.network_key = self.config.nwskey
            self.apps_key = self.config.appskey
        elif self.config.auth == AUTH_OTAA:
            self.appeui = self.config.appeui
            self.deveui = self.config.deveui
            self.appkey = self.config.appkey
        assert self.get_agc_auto_on() == 1
        self.gps_serial = Serial(
            self.config.gps_serial_port,
            self.config.gps_baud_rate,
            timeout=self.config.gps_serial_timeout)
        self.gps_serial.flush()

        # for downlink messages
        self.downlinkCallback=None

    def setDownlinkCallback(self,func=None):
        """
        Configure the callback function which will receive
        two parameters: decodedPayload and mtype.

        decodedPayload will be a bytearray.
        mtype will be MHDR.UNCONF_DATA_DOWN or MHDR.CONF_DATA_DOWN.

        See test_downlink.py for usage.

        func: function to call when a downlink message is received
        """
        if hasattr(func,'__call__'):
            self.logger.info("Setting downlinkCallback to %s",func)
            self.downlinkCallback=func
        else:
            self.logger.info("downlinkCallback is not callable")


    def _choose_freq(self, join=False):
        if join:
            available = JOIN_FREQS
        else:
            available = LORA_FREQS
        freq = available[randrange(len(available))]#Pick a random frequency
        self.set_mode(MODE.SLEEP)
        self.set_freq(freq)
        self.logger.info("Frequency = %s", freq)


    def _read_frame_count(self):
        """
            Read the frame count from file - if no file present assume it's 1
        """
        self.frame_count = self.config.get_fcount()

    def _save_frame_count(self):
        """
            Saves the frame count out to file so that check in ttn can be enabled
            If the file doesn't exist then create it
        """
        self.config.save_fcount(self.frame_count)

    def on_rx_done(self):
        """
            Callback on RX complete, signalled by I/O
        """
        self.clear_irq_flags(RxDone=1)
        self.logger.debug("Recieved message")
              
        try:

            payload = self.read_payload(nocheck=True)
            
            if payload is None:
                self.logger.info("payload is None")
                return
           
            if not self.config.joined():
               # not joined yet
               self.logger.info("processing JOIN_ACCEPT payload")
               lorawan = lorawan_msg([], self.appkey)
               lorawan.read(payload)
               decodedPayload=lorawan.get_payload()
            else:
               # joined
               self.logger.info("processing payload after joined")               
               lorawan = lorawan_msg(self.network_key, self.apps_key)
               lorawan.read(payload)
               decodedPayload=lorawan.get_payload()
        
        except Exception as e:
            self.logger.exception("Exception %s",e)
            return
        
        mtype=lorawan.get_mhdr().get_mtype()
        self.logger.debug("Processing message: MDHR version %s mtype %s payload %s ",lorawan.get_mhdr().get_mversion(), mtype,decodedPayload)

        if mtype == MHDR.JOIN_ACCEPT:
            self.logger.debug("Processing JOIN_ACCEPT")
            #It's a response to a join request
            lorawan.valid_mic()
            self.device_addr = lorawan.get_devaddr()
            self.logger.info("Device: %s", self.device_addr)
            self.network_key = lorawan.derive_nwskey(self.devnonce)
            self.logger.info("Network key: %s", self.network_key)
            self.apps_key = lorawan.derive_appskey(self.devnonce)
            self.logger.info("APPS key: %s", self.apps_key)
            self.frame_count = 1
            self.config.save_credentials(
                    self.device_addr, self.network_key,
                    self.apps_key, self.frame_count)
            return
        
        elif mtype==MHDR.UNCONF_DATA_DOWN or mtype==MHDR.CONF_DATA_DOWN:
            self.logger.debug("Downlink data received")
            
            if self.downlinkCallback is not None:
                lorawan.valid_mic()
                self.downlinkCallback(decodedPayload,mtype)
            return
        else:
            self.logger.debug("Unexpected message type %s",mtype)
        

        
    def on_tx_done(self):
        """
            Callback on TX complete is signaled using I/O
        """
        self.logger.debug("TX Complete")
        self.transmitting = False
        self.clear_irq_flags(TxDone=1)
        self.set_mode(MODE.STDBY)
        self.set_dio_mapping([0, 0, 0, 0, 0, 0])
        self.set_invert_iq(1)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)


    def join(self):
        """
            Perform the OTAA auth in order to get the keys requried to transmit
        """
        self.devnonce = [randrange(256), randrange(256)] #random nonce
        self.logger.debug("Nonce = %s", self.devnonce)
        if self.config.auth == AUTH_ABP:
            self.logger.info("Using ABP no need to Join")
        elif self.config.auth == AUTH_OTAA:
            if self.config.joined():
                self.logger.info("Using cached details")
                self.logger.debug(self.config.devaddr)
                self.device_addr = self.config.devaddr
                self.network_key = self.config.nwkskey
                self.apps_key = self.config.appskey
            else:
                self.logger.debug("Performing OTAA Join")
                appkey = self.appkey
                appeui = self.appeui
                deveui = self.deveui
                self.logger.info("App key = %s", appkey)
                self.logger.info("App eui = %s", appeui)
                self.logger.info("Dev eui = %s", deveui)
                self._choose_freq(True)
                lorawan = lorawan_msg(appkey)
                lorawan.create(
                    MHDR.JOIN_REQUEST,
                    {'deveui': deveui, 'appeui': appeui, 'devnonce': self.devnonce})
                self.write_payload(lorawan.to_raw())
                self.set_dio_mapping([1, 0, 0, 0, 0, 0])
                self.set_mode(MODE.TX)
                self.transmitting = True
        else:
            self.logger.error("Unknown auth mode")
            return

    def registered(self):
        """
            Returns true if either ABP is used for auth, in which case registration
            is hardcoded, otherwise check that join has been run
        """
        return self.device_addr is not None

    def send_bytes(self, message):
        """
            Send a list of bytes over the LoRaWAN channel
        """
        attempt = 0
        if self.network_key is None or self.apps_key is None: # either using ABP / join has  run
            raise DraginoError("No network and/or apps key")
        while attempt <= self.lora_retries: # try a couple of times because of
            self._choose_freq()
            attempt += 1 #  intermittent malformed packets nasty hack
            try: #shouldn't be needed
                lorawan = lorawan_msg(self.network_key, self.apps_key)
                lorawan.create(
                    MHDR.UNCONF_DATA_UP,
                    {'devaddr': self.device_addr,
                     'fcnt': self.frame_count,
                     'data': message})
                self.logger.debug("Frame count %d", self.frame_count)
                self.frame_count += 1
                self.write_payload(lorawan.to_raw())
                self.logger.debug("Packet = %s", lorawan.to_raw())
                self.set_dio_mapping([1, 0, 0, 0, 0, 0])
                self.set_mode(MODE.TX)
                self.transmitting = True
                self.logger.info(
                    "Succeeded on attempt %d/%d", attempt, self.lora_retries)
                self._save_frame_count()
                return
            except ValueError as err:
                self.logger.error(str(err))
                raise DraginoError(str(err)) from None
            except MalformedPacketException as exp:
                self.logger.error(exp)
            except KeyError as err:
                self.logger.error(err)

    def send(self, message):
        """
            Send a string over the channel
        """
        self.send_bytes(list(map(ord, str(message))))

    def get_gps(self):
        """
            Get the GPS position from the dragino,
            waits for the specified timeout and then gives up
        """
        start = datetime.utcnow()
        end = start + timedelta(seconds=self.config.gps_wait_period)
        self.logger.info(
            "Waiting for %d seconds until %s", self.config.gps_wait_period, end)
        msg = None

        while datetime.utcnow() < end:
            try:
                # read the serial port, convert to a string
                gps_data = self.gps_serial.readline().decode()
            except UnicodeDecodeError:
                #not yet got valid data from gps
                continue
            gps_data_arr = gps_data.split(",")
            if gps_data_arr[0] == "$GPGGA": #It's a position string
                #print(gps_data)
                msg = pynmea2.parse(gps_data)
                break
        # this will be None if no message is decoded, otherwise it'll contain the information
        return msg

class DraginoError(Exception):
    """
        Error class for dragino class
    """

class DraginoConfig():
    """
        Reads an ini file containing the configuration for the dragino board
    """
    def __init__(self, config_file, log_level=DEFAULT_LOG_LEVEL):
        """
            Read in the config and create the object
        """
        self.logger = logging.getLogger("DraginoConfig")
        self._config_file = config_file
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
        self.logger.setLevel(log_level)
        try:
            config = ConfigObj(config_file)
            self._config = config
            self._config.filename = config_file
            self.gps_baud_rate = int(config["gps_baud_rate"])
            self.gps_serial_port = config["gps_serial_port"]
            self.gps_serial_timeout = int(config["gps_serial_timeout"])
            self.gps_wait_period = int(config["gps_wait_period"])
            self.spreading_factor = int(config["spreading_factor"])
            self.max_power = int(config["max_power"], 16)
            self.output_power = int(config["output_power"], 16)
            self.sync_word = int(config["sync_word"], 16)
            self.rx_crc = bool(config["rx_crc"])
            self.fcount_filename = config["fcount_filename"]
            auth = config["auth_mode"]
            if auth.upper() == "ABP":
                self.logger.info("Using ABP mode")
                self.auth = AUTH_ABP
                self.devaddr = self._convert_array(config["devaddr"])
                self.nwskey = self._convert_array(config["nwskey"])
                self.appskey = self._convert_array(config["appskey"])
            elif auth.upper() == "OTAA":
                self.logger.info("Using OTAA mode")
                self.auth = AUTH_OTAA
                self.deveui = self._convert_array(config["deveui"])
                self.appeui = self._convert_array(config["appeui"])
                self.appkey = self._convert_array(config["appkey"])
                try:
                    self.devaddr = self._convert_array(config["devaddr"], 10)
                    self.nwkskey = self._convert_array(config["nwkskey"], 10)
                    self.appskey = self._convert_array(config["appskey"], 10)
                except (KeyError, ValueError):
                    self.logger.warning("Unable to read session details")
                    self.devaddr = None
                    self.nwkskey = None
                    self.appskey = None
            else:
                self.logger.critical("Unsupported auth mode chosen: %s", auth)
                raise DraginoError("Unsupported auth mode")
            try:
                self.fcount = int(config["fcount"])
            except KeyError:
                self.fcount = self._read_legacy_fcount() #load from previos file
                self.save()
            self.logger.debug("GPS Baud Rate: %d", self.gps_baud_rate)
            self.logger.debug("GPS Serial Port: %s", self.gps_serial_port)
            self.logger.debug("GPS Serial Timeout: %s", self.gps_serial_timeout)
            self.logger.debug("GPS Wait Period: %d", self.gps_wait_period)
            self.logger.debug("Spreading factor: %d", self.spreading_factor)
            self.logger.debug("Max Power: %02X", self.max_power)
            self.logger.debug("Output Power: %02X", self.output_power)
            self.logger.debug("Sync Word: %02X", self.sync_word)
            self.logger.debug("RX CRC: %s", str(self.rx_crc))
            self.logger.debug("Frame Count Filename: %s", self.fcount_filename)
            self.logger.debug("Auth mode: %s", self.auth)
            if self.auth == AUTH_ABP:
                self.logger.debug(
                    "Device Address: %s", " ".join(
                        '{:02X}'.format(x) for x in self.devaddr))
                self.logger.debug(
                    "Network Session Key: %s", " ".join(
                        '{:02X}'.format(x) for x in self.nwskey))
                self.logger.debug(
                    "App Session Key: %s", " ".join(
                        '{:02X}'.format(x) for x in self.appskey))
            elif self.auth == AUTH_OTAA:
                self.logger.debug(
                    "Device EUI: %s", " ".join(
                        '{:02X}'.format(x) for x in self.deveui))
                self.logger.debug(
                    "App EUI: %s", " ".join(
                        '{:02X}'.format(x) for x in self.appeui))
                self.logger.debug(
                    "App Key: %s", " ".join(
                        '{:02X}'.format(x) for x in self.appkey))
        except KeyError as err:
            self.logger.critical("Missing required field %s", str(err))
            raise DraginoError(err) from None
        except ValueError as err:
            self.logger.critical("Unable to parse number %s", str(err))
            raise DraginoError(err) from None

    def joined(self):
        joined = bool(self.appskey) and bool(self.devaddr) and bool(self.nwkskey)
        self.logger.debug("Joined %r", joined)
        return joined

    def save(self):
        """
            save back out to file - need to update the object with the parameters
            that can legitimately have changed
        """
        self._config["fcount"] = self.fcount
        if self.auth == AUTH_OTAA: #have session params to save
            self._config["appskey"] = self.appskey
            self._config["devaddr"] = self.devaddr
            self._config["nwkskey"] = self.nwkskey
        self._config.write()

    def save_credentials(self, devaddr, nwskey, appskey, fcount):
        self.devaddr = devaddr
        self.nwkskey = nwskey
        self.appskey = appskey
        self.fcount = fcount
        self.save()

    def save_fcount(self, fcount):
        self.logger.debug("Saving fcount")
        self.fcount = fcount
        self.save()

    def get_fcount(self):
        return self.fcount

    def _read_legacy_fcount(self):
        fname = self._config["fcount_filename"]
        if not os.path.isfile(fname):
            self.logger.warning("No frame count file available")
            return 1
        self.logger.info("Reading Frame count from: %s", fname)
        try:
            with open(fname, "r") as f_handle:
                return int(f_handle.readline())
        except (IOError, ValueError) as exp:
            self.logger.error("Unable to open fcount file. Resettting count")
            self.logger.error(str(exp))
            return 1

    def _convert_array(self, arr, base=16):
        """
            Takes an array of hex strings and converts them into integers
        """
        new_arr = []
        for item in arr:
            new_arr.append(int(item, base))
        self.logger.debug("Converted %d/%d items", len(new_arr), len(arr))
        return new_arr
