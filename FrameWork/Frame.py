
import errno
import getpass
import json
import os
import re
import socket
import time
import threading
import pprint
import xmltodict
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Union
from statistics import mean
import paramiko
import yaml
from dateutil import parser
from lxml import etree
from robot.libraries.BuiltIn import BuiltIn, RobotNotRunningError, _Control

from framework.libraries.common.logger import Logger as logger
import framework.libraries.common.log_transfer as lgtr
import framework.libraries.common.profile_translation as ptr
import framework.libraries.common.utils as utils
from framework.keywords.keywords import Keywords
from framework.libraries.common.config_modification import Component, ConfigModification
from framework.libraries.common.exceptions import (
    ComponentPMFailure,
    ComponentStopFailed,
    FrameworkException,
    IperfException,
    ComponentStartFailed,
)
from framework.libraries.common.report_data import ReportData
from framework.libraries.common.ssh_connection import SSHConnection
from framework.libraries.common.xml_modifier import XMLModification
from framework.libraries.components.base_components import (
    DeploymentEnv,
    OperationalStatus,
    OamaState,
)
from framework.libraries.components.ue.android_ue import AndroidUE
from framework.libraries.components.ue.keysight_ue import KeySightUE
from framework.libraries.components.ue.podman_ue import State
from framework.libraries.components.ue.simnovus_ue import SimnovusUE
from framework.libraries.components.ue.accuver_ue import AccuverUE
from framework.libraries.components.ue.tm500_ue import TM500UE
from framework.libraries.managers.log_manager import LogManager
from framework.libraries.managers.TrafficManager import TrafficManager
from framework.global_variables import Global_Variables
from framework.keywords.RemotePdu import RemotePduSnmp
import framework.libraries.common.data_lake as dlk
from framework.libraries.common.data_lake import ActionType


class CoreKeywords(Keywords):
    """
    The class includes the keywords to start stop and interact
    with the testing components
    """ 

    ROBOT_LIBRARY_SCOPE = "GLOBAL"
    test_case_directory_path = ""
    namespaces = {
        "netconf": "urn:ietf:params:xml:ns:netconf:base:1.0",
        "5gran": "urn:3gpp:tsg:sa5:nrm:ngran",
        "3gpp_me": "urn:3gpp:sa5:_3gpp-common-managed-element",
        "fm_dvs": "urn:dell:_3gpp-common-fm",
    }

    def __init__(self) -> None:
        """
        Do the init based on the TL type and the node type
        """
        self.testline = Keywords.get_testline()
        self.log_manager = LogManager()
        self.traffic_manager = TrafficManager()
        try:
            self.pcap_capture_components = BuiltIn().get_variable_value(
                "${PCAP_COMPONENTS}"
            )
            if not BuiltIn().get_variable_value("${SKIP_TEST}"):
                BuiltIn().set_suite_variable("${SKIP_TEST}", "False")
        except RobotNotRunningError:
            self.pcap_capture_components = os.environ.get("PCAP_COMPONENTS")

        self.test_case_control = _Control()
        self.component_obj_dict = {}
        self.modified_components = {}
        self.txt_modified_components = {}
        self.traffic_type = None
        self.list_components_started = []
        self.alarm_start_time = ""
        self.signaling_thread = None
        self.android_profile_thread_instance = logger()

    @staticmethod
    def update_yaml_env(inventory_yaml_file: str) -> dict:
        """
        Description:
            This keyword provide method to update the environment variable to yaml file.
        Args:
            yaml_file_path (str): the direction of the yaml file.
        """
        # pattern to extract env variables
        env_pattern = re.compile(r".*?\${(.*?)}.*?")

        # Define function to add constructor yaml
        def env_constructor(loader, node):
            value = loader.construct_scalar(node)
            for env_var in env_pattern.findall(value):
                if os.environ.get(env_var):
                    value = value.replace(f"${{{env_var}}}", os.environ.get(env_var))
                elif "PASS" in env_var.upper():
                    logger.info(
                        f"{inventory_yaml_file} contain Environment Variable {env_var} does not exist in test runner!",
                        also_console=True,
                    )
                    pw = getpass.getpass(f"Please input password for {env_var}:")
                    value = value.replace(f"${{{env_var}}}", pw)
                    os.environ[env_var] = pw
                else:
                    logger.info(
                        f"{inventory_yaml_file} contain Environment Variable {env_var} does not exist in test runner!",
                        also_console=True,
                    )
                    logger.info(f"Please input value for {env_var}:", also_console=True)
                    input_value = input()
                    value = value.replace(f"${{{env_var}}}", input_value)
                    os.environ[env_var] = input_value
            return value

        try:
            yaml.add_implicit_resolver(
                yaml.resolver.BaseResolver.DEFAULT_SCALAR_TAG,
                env_pattern,
                None,
                yaml.loader.SafeLoader,
            )
            yaml.add_constructor(
                yaml.resolver.BaseResolver.DEFAULT_SCALAR_TAG,
                env_constructor,
                yaml.loader.SafeLoader,
            )
            with open(inventory_yaml_file, "r") as f:
                yaml_dict = dict(next(yaml.full_load_all(f)))
        except Exception as e:
            raise FrameworkException(
                f"Fail to update the yaml inventory file: {inventory_yaml_file} due to: {e}"
            )
        return yaml_dict

    def get_testline(self):
        return self.testline

    def check_cell_up(self, component_id: str = None, num_cells: int = 1, timeout: int = 240) -> None:
        """
        Description:
            Confirms and prints whether the DU Cell is UP

        Parameters:
            component_id(str): The component id of DU
            num_cells(int): number cells need to up
            timeout(int): Time to check cell up. Default is 240s

        Returns:
            None
        """
        logger.info("Checking if DU Cell is Up", also_console=True, banner=True)
        return_status = False
        if component_id is None:
            logger.info(
                "====== No component id provided. Will check status of all DU",
                also_console=True,
            )
            DU_components = self.testline.get_components_by_type("DU")
            for DU in DU_components:
                self.check_cell_up(DU.id, num_cells, timeout)
            return
        logger.info(f"====== {component_id}: Check cell up", also_console=True)
        DU_component = self.testline.get_component_by_id(component_id)
        logger.info(
            f"Check cell up with num_cells is {num_cells}, default is 1",
            also_console=True,
            )
        start_time = time.time()
        # Check that cells come up until timeout
        while time.time() < start_time + timeout:
            actual_num_cells = DU_component.get_number_cell_up()
            if actual_num_cells >= num_cells:
                return_status = True
                break
        if return_status:
            logger.info(
                f"====== Confirmed: {component_id} cell(s) is up and running with {actual_num_cells}cell!",
                also_console=True,
            )
        else:
            raise Exception(
                f"{component_id} cell(s) is not up and running as expected, please check for errors"
            )

    def restart_components(
        self, *components_ids: str, num_cells: int = 1, check_cell_up: bool = True
    ) -> None:
        """
        Description:
            This function will restart the components of the Test Line.
        Parameters:
            components_ids (list): list of component id which need to be restarted
                i.e: UE1, DU1, CUUP1, CUCP1 => It will stop UE1, DU1, CUUP1, CUCP1 => then start CUCP1, CUUP1, DU1, UE1
            num_cells (int): The number of cells for which we want to modify the config files, default=1
            check_cell_up (bool): a flag to check whether cell is up on DU component, default=True
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        logger.info(
            "====== Restarting the components with the modified configuration\n",
            also_console=True,
        )
        # TODO As a workaround till OAM team supports reconnection in OAMA, restart all the components.
        self.test_line_stop()
        self.test_line_start(
            num_cells, components_ids=None, check_cell_up=check_cell_up
        )

    def configure_component(self, component: str, config: str = "", config_file: str = "", id: str = None) -> None:
        """
        Description:
            This function will configure the components of the Test Line. Intended for DU/CU. Parameters config or config_file must be provided. If both are provided, config file will be used
        Parameters:
            component: component to configure. must have config method defined.
            config_file (str): Name of file to apply as config
            config (str): text to apply as a config
            id (str): component id, if none is set will do for all component of a given type. Default value is None
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        logger.info(f"Configuring Component {component}", also_console=True, banner=True)
        try:
            if config_file != "":
                with open(config_file, "r") as f:
                    config = f.read()
        except Exception as e:
            raise FrameworkException(
                f"Failed to open config files of {component} due to: {e}"
            )
        # Components in testline object:
        try:
            if component in ["CORE", "CUUP", "CUCP", "DU", "UE", "MinervaL1", "RU"]:
                if id is None:
                    testline_components = self.testline.get_components_by_type(
                        component
                    )
                    for testline_component in testline_components:
                        testline_component.configure(config)
                else:
                    testline_component = self.testline.get_component_by_id(id)
                    testline_component.configure(config)
            else:
                raise Exception(f"{component} does not support configure function")
        except Exception as e:
            raise FrameworkException(f"Failed to configure {component} due to: {e}")

    def set_custom_config_component(
        self,
        component_id: str,
        custom_config_file_name: str,
        core_component: str = None,
    ) -> None:
        """
        Description:
            Set custom netconf file to component object before starting test line.

        Args:
            component_id (str): the component id want to update the config file.
            custom_config_file_name (str): the custom config file name want to start with component_id
            core_component (str): the component of core want to update the config file. (Ex: amf, smf, upf, xfe)

        Exceptions:
            raise FrameworkException: if component object do not support to set custom config file name.
        """
        try:
            component_obj: object = self.testline.get_component_by_id(component_id)
            # Update net-config in component object
            if core_component:
                config_file_name_core = f"config_file_name_{(core_component).lower()}"
                if hasattr(component_obj, config_file_name_core):
                    setattr(
                        component_obj, config_file_name_core, custom_config_file_name
                    )
                else:
                    raise FrameworkException(
                        f"Component ID: {component_id} do not support to set custom config file name: {custom_config_file_name}"
                    )
            elif hasattr(component_obj, "config_file_name"):
                component_obj.config_file_name = custom_config_file_name
            else:
                raise FrameworkException(
                    f"Component ID: {component_id} do not support to set custom config file name: {custom_config_file_name}"
                )
        except Exception as e:
            raise FrameworkException(
                f"Failed to set netconf for applying to start {component_id} due to: {e}"
            )

    def generate_nrQosConfig_block(self, component_id: str, values_dict: dict) -> None:
        """
        Description:
            Generate new nrQosconfig block base on the existed block in xml config.
        Parameters:
            component_id (str): The component id want to get xml file.
                i.e: CUCP1
            values_dict (dict, optional): The dictionary of the key and values to change in the nrQosconfig block.
                i.e: {"cqi": [6,7,8,9], "qos-group-index":[4,5,6,]}
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        logger.info("Generating nrQosconfig Block", also_console=True, banner=True)
        component = self.testline.get_component_by_id(component_id)

        block_xpath = ".//urn_cucp_ns:qos-config-group"

        if Keywords.test_case_directory_path:
            test_runner_config_file_path = f"{Keywords.test_case_directory_path}/{component.type}/{component.id}/Config/"
        else:
            test_runner_config_file_path = os.getcwd()
        config_file_dir = os.path.join(
            component.config_file_path, component.config_file_name
        )
        lgtr.copy_file_scp(
            component.connection, config_file_dir, test_runner_config_file_path
        )
        xml_file = os.path.join(
            test_runner_config_file_path, component.config_file_name
        )
        xml_modification = XMLModification(xml_file, is_multiple_root=True)
        element_list = xml_modification.get_element(block_xpath)
        # """
        # element_list is a list of <qos-config-group> block as below:
        # <qos-config-group>
        #    <qci>9</qci>
        #    <qos-group-index>1</qos-group-index>
        # </qos-config-group>
        # """
        if not element_list:
            raise FrameworkException(
                f"Could not find element {block_xpath} in config file {component.config_file_name}"
            )

        formatted_values = []
        for key_name in values_dict:
            for index, key_value in enumerate(values_dict[key_name]):
                if index not in formatted_values:
                    formatted_values.append(index)
                    xml_modification.copy_element(
                        element_list[0], element_list[0].getparent()
                    )
                # After copy element, the number of <qos-config-group> block increases.
                # Need to increase index + 1 since xpath element index started with 1.
                xml_modification.update_value(
                    f"({key_name})[{len(element_list) + index + 1}]", str(key_value)
                )

        modified_xml_file = f"RATE_N_Blocks_{component.config_file_name}"
        test_runner_modified_xml_file_path = os.path.join(
            test_runner_config_file_path, modified_xml_file
        )
        xml_modification.export_xml_file(test_runner_modified_xml_file_path)
        lgtr.copy_file_scp(
            component.connection,
            test_runner_modified_xml_file_path,
            f"{component.config_file_path}",
            method="put",
        )
        component.modified_config_file = modified_xml_file

    def generate_config_bring_up_multiple_cells(
        self, num_cells: int, component_ids: List = None
    ) -> None:
        """
        Description:
            Generate the config to bring up N Cells.
        Parameters:
            num_cells (int): The specific number of Cell want to bring up.
            component_ids (List): The list IDs of components want to bring up multiple Cells. Default is None
        """
        # Generate custom yaml file to bring up multiple Cells
        if Keywords.test_case_directory_path:
            custom_yaml_file = f"{Keywords.test_case_directory_path}/multiple_cells.yaml"
        else:
            custom_yaml_file = os.path.join(os.getcwd(), "multiple_cells.yaml")
        ConfigModification().generate_custom_yaml_bring_up_multiple_cells(
            num_cells, custom_yaml_file
        )

        comp_ids = []
        if component_ids:
            # To bring up multiple cells, DU and CUCP configuration need to update
            # Check both DU and CUCP component types are provided
            list_comp_types = []
            for id in component_ids:
                comp = self.testline.get_component_by_id(id)
                list_comp_types.append(comp.type)
            if "CUCP" or "DU" not in list_comp_types:
                raise FrameworkException(
                    "Both CUCP and DU component ids must be provided. Please check the component_ids argument."
                )
            comp_ids = component_ids
        else:
            for component in self.testline.components:
                if component.type == "DU" or component.type == "CUCP":
                    comp_ids.append(component.id)
        # Modify configuration file with xpath
        self.modify_config_file_xpath(*comp_ids, yaml_template=custom_yaml_file)

    def return_minerva_ip(self, component: str) -> str:
        L1 = self.testline.get_component_by_id(component)
        return L1.check_l1_ip_from_dhcp_server()

    def check_config(
        self, component: str, xpath: str, match: str, retry_time: int = 5, id: str = None
    ) -> None:
        """
        Description:
            This function will check if netconf config (including operational data) is matching to "match".
        Parameters:
            component (str): component will check configure. Component[CUCP, CUUP, DU] must have config method defined [netconf_console_path].
            xpath (str): xpath to narrow config response.
            match (str): string to check for in response:Locked,Idle,Unlocked,Enabled,.....
            retry_time(int): Adding retry timer which will retry the netconf rpc request few more times until retry_timer times out
            id (str): component id, if none is set will do for all component of a given type. Default value is None
                      Note that with component is RU_SIM, id should be id of DU
        Returns:
            None: This function only executes the codes and does not return any value.
        Example:
            Check Config    DU    */GNBDUFunction/NRCellDU[id=0]/attributes/administrativeState    Locked
        """
        logger.info("Checking Netconf Configuration", also_console=True, banner=True)
        if id is None:
            if component == "RU_SIM":
                testline_components = self.testline.get_components_by_type("DU")
            else:
                testline_components = self.testline.get_components_by_type(component)
            for testline_component in testline_components:
                self.check_config(
                    component, xpath, match, retry_time, id=testline_component.id
                )
            return
        logger.info(
            f"====== Check Config: component: {component} - id: {id}, xpath: {xpath}, expected string: {match}",
            also_console=True,
        )
        testline_component = self.testline.get_component_by_id(id)
        nc = Global_Variables.netconf_console_path
        # As per [MP-87767], we need to get sync-state from RU side, other states can be checked from DU side
        if component == "RU":
            sut = testline_component.ip
            oam_port = str(Global_Variables.oam_port)
            # Get ru-instance-id and add the path before xpath
            ru_instance_id = testline_component.ru_instance_id
            netconf_cmd = (
                f"{nc}netconf-console --host={sut} --user=netconf --privKeyType=rsa --privKeyFile={Global_Variables.NETCONF_PRIVATE_KEYPATH} "
                f"--port={oam_port} --get -x /aggregated-o-ru/aggregation[ru-instance={str(ru_instance_id)}]/dvs-agg-model"
                f"{xpath}"
            )
        elif component == "RU_SIM":
            if "DU" not in testline_component.type:
                raise FrameworkException(
                    f"RU_SIM component configuration must be checked from DU server. Now component id={id}, please check..."
                )
            sut = testline_component.oam_ip
            ru_sim_port = str(testline_component.ru_sim_port)
            netconf_cmd = (
                f"{nc}netconf-console --host={sut} --user=admin --password=admin "
                f"--port={ru_sim_port} --get -x {xpath}"
            )
        else:
            sut = testline_component.ip
            oam_port = str(Global_Variables.oam_port)
            netconf_cmd = (
                f"{nc}netconf-console --host={sut} --port={oam_port} --user=netconf "
                f"--privKeyType=rsa --privKeyFile={Global_Variables.NETCONF_PRIVATE_KEYPATH} --get -x {xpath}"
            )

        try:
            ret_value_netconf = utils.check_netconf_value(
                connection=testline_component.connection,
                netconf_cmd=netconf_cmd,
                timeout=retry_time,
                expected_match=match,
                unexpected_match=None,
            )
            if ret_value_netconf:
                logger.info(f"{match} found in netconf response", also_console=True)
            else:
                raise Exception(
                    f"Component: {component} - id: {id}: {match} not found in netconf response"
                )

        except Exception as e:
            raise Exception(
                f"Component: {component} - id: {id}: Could not get config due to error: {e}"
            ) from e

    def retry_check_config(self, retry_time: int, component_id: str, get_cmd: str, match: str) -> bool:
        """
        Description:
            This method will check config get from component is match or not
        Parameters:
            retry_time (int): time to check config
            component_id (str): component id want to check the config
            get_cmd (str): command to get config from the component id
            match (str): string want to check in the response from config
        Returns:
            bool: True if match string is found in the response. Otherwise return False
        """
        start_time = time.time()
        netconf_match_found = False
        while time.time() < start_time + retry_time:
            netconf_response = self.testline.get_component_by_id(
                component_id
            ).connection.sendCommand_shell(get_cmd)
            netconf_response = netconf_response.replace("&gt;", ">")
            netconf_response = netconf_response.replace("&lt;", "<")
            if match in netconf_response:
                netconf_match_found = True
                break
        return netconf_match_found

    def lock_cell(self, cell_num: int, id: str = None, managedelement_id: str = "0", gnbdufunction_id: str = "0") -> None:
        """
        Description:
            This function will lock cell on DU.
        Parameters:
            cell_num (int): number cell to lock (zero-indexed to match netconf).
            id (str): component id, if none is set will do do for all component of a given type. Default value is None
            managedelement_id (str): managed element id. Default value is 0
            gnbdufunction_id (str): gnbdu function id. Default value is 0
        Returns:
            None: This function only executes the codes and does not return any value.
        Example:
            Lock Cell    1
        """
        logger.info(
            f"====== Lock cell: cell_num: {cell_num} in {f'component id: {id}' if id else 'ALL DU'}",
            also_console=True,
        )
        self.configure_component(
            "DU",
            config=(
                f'<ManagedElement xmlns="urn:3gpp:sa5:_3gpp-common-managed-element"> <id>{managedelement_id}</id> '
                f'<GNBDUFunction xmlns="urn:3gpp:sa5:_3gpp-nr-nrm-gnbdufunction"> <id>{gnbdufunction_id}</id> '
                f'<NRCellDU xmlns="urn:3gpp:sa5:_3gpp-nr-nrm-nrcelldu"> <id>{cell_num}</id> '
                "<attributes> <administrativeState>LOCKED</administrativeState> "
                "</attributes> </NRCellDU> </GNBDUFunction> </ManagedElement>"
            ),
            id=id,
        )
        dlk.publish_action_to_datalake(action_name=ActionType.LOCK_CELL_ACTION,
                                       value="1",
                                       dn=f"ManagedElement={managedelement_id},GNBDUFunction={gnbdufunction_id},NRCellDU={cell_num}")

    def unlock_cell(self, cell_num: int, id: str = None, managedelement_id: str = "0", gnbdufunction_id: str = "0") -> None:
        """
        Description:
            This function will unlock cell on DU.
        Parameters:
            cell_num (int): number cell to unlock (zero-indexed to match netconf).
            id (str): component id, if none is set will do for all component of a given type. Default value is None
            managedelement_id (str): managed element id. Default value is 0
            gnbdufunction_id (str): gnbdu function id. Default value is 0
        Returns:
            None: This function only executes the codes and does not return any value
        Example:
            Unlock Cell    2
        """
        logger.info(
            f"====== Unlock cell: cell_num: {cell_num} in {f'component id: {id}' if id else 'ALL DU'}",
            also_console=True,
        )
        self.configure_component(
            "DU",
            config=(
                f'<ManagedElement xmlns="urn:3gpp:sa5:_3gpp-common-managed-element"> <id>{managedelement_id}</id> '
                f'<GNBDUFunction xmlns="urn:3gpp:sa5:_3gpp-nr-nrm-gnbdufunction"> <id>{gnbdufunction_id}</id> '
                f'<NRCellDU xmlns="urn:3gpp:sa5:_3gpp-nr-nrm-nrcelldu"> <id>{cell_num}</id> <attributes> '
                "<administrativeState>UNLOCKED</administrativeState> </attributes> "
                "</NRCellDU> </GNBDUFunction> </ManagedElement>"
            ),
            id=id,
        )
        dlk.publish_action_to_datalake(action_name=ActionType.UNLOCK_CELL_ACTION,
                                       value="1",
                                       dn=f"ManagedElement={managedelement_id},GNBDUFunction={gnbdufunction_id},NRCellDU={cell_num}")

    def delete_cell(self, cell_num_range: str, component: str = "DU", id: str = None) -> None:
        """
        Description:
            This function will delete the cell on DU.
        Parameters:
            cell_num_range (str): the range of the number the Cells to delete
            i.e.
                cell_num_range= "1" -> ["1"]
                cell_num_range= "1-5" -> (1,2,3,4,5)
                cell_num_range= "1,2,5,6" -> ["1","2","5","6"]
            component (str): the string name of the component want to delete Cell. default = "DU"
            id (str): component id, if none is set will do for all component of a given type. Default value is None
        Return:
            N/A: This function only executes the codes and does not return any value
        """
        if id is None:
            testline_components = self.testline.get_components_by_type(component)
            for testline_component in testline_components:
                self.delete_cell(
                    cell_num_range, component=component, id=testline_component.id
                )
            return
        logger.info(
            f"Delete Cell: cell_num_range: {cell_num_range}, component: {component}, component_id: {id}",
            also_console=True,
        )
        testline_component = self.testline.get_component_by_id(id)
        config_file_path = testline_component.config_file_path
        delete_cell_path = "resources/netconf/delete_cell_default_cfg.xml"
        modify_delete_xml = XMLModification(delete_cell_path, is_multiple_root=True)

        try:
            # Parse cell list
            if re.search(r"\d+-\d+", cell_num_range):
                cell_list = range(
                    int(cell_num_range.split("-")[0]),
                    int(cell_num_range.split("-")[1]) + 1,
                )
            elif re.search(r"\d+,\d+", cell_num_range):
                cell_list = cell_num_range.split(",")
            elif re.search(r"\d+", cell_num_range):
                cell_list = [cell_num_range]
            else:
                raise TypeError("Do not support this cell number range type!")

            # Do deleting cell
            for cell_num in cell_list:
                nc = Global_Variables.netconf_console_path
                get_NRCell_id_cmd = (
                    f"{nc}/netconf-console --host={testline_component.oam_ip} --port={Global_Variables.oam_port} "
                    f"--user=netconf --privKeyType=rsa --privKeyFile={Global_Variables.NETCONF_PRIVATE_KEYPATH} --get -x */*/NRCellDU/id"
                )
                output = testline_component.connection.sendCommand_shell(
                    get_NRCell_id_cmd
                )
                if re.search(rf"<NRCellDU.*>\s+<id>{cell_num}<\/id>", output):
                    logger.info(
                        f"Component: {component} - id {id}: Cell {cell_num} exists!!!",
                        also_console=True,
                    )
                else:
                    raise Exception(
                        f"Component: {component} - id {id}: Cell {cell_num} does not exist, Cannot delete! with id {id}"
                    )

                # Modify the delete cell xml file
                modify_delete_xml.update_value(
                    ".//nrcelldu:NRCellDU[@operation='delete']/nrcelldu:id",
                    str(cell_num),
                )
                test_runner_config_folder_path = Global_Variables.log_dir
                if not os.path.exists(test_runner_config_folder_path):
                    os.makedirs(test_runner_config_folder_path)
                xml_file_path = f"{test_runner_config_folder_path}/delete_cell_{cell_num}_minimal.xml"
                modify_delete_xml.export_xml_file(xml_file_path)

                # Copy to the test line to apply netconf file.
                lgtr.copy_file_scp(
                    testline_component.connection,
                    xml_file_path,
                    f"{config_file_path}",
                    method="put",
                )

                utils.apply_netconf_config(
                    connection=testline_component.connection,
                    netconf_console_path=Global_Variables.netconf_console_path,
                    oam_ip=testline_component.oam_ip,
                    oam_port=Global_Variables.oam_port,
                    config_file=f"{config_file_path}/delete_cell_{cell_num}_minimal.xml",
                )

                # Verify the CELL was deleted
                get_NRCell_id_cmd = (
                    f"{nc}/netconf-console --host={testline_component.oam_ip} "
                    f"--port={Global_Variables.oam_port} --user=netconf --privKeyType=rsa "
                    f"--privKeyFile={Global_Variables.NETCONF_PRIVATE_KEYPATH} --get -x */*/NRCellDU/id"
                )
                output = testline_component.connection.sendCommand_shell(
                    get_NRCell_id_cmd
                )
                if not re.search(rf"<NRCellDU>\s+<id>{cell_num}<\/id>", output):
                    logger.info(
                        f"Component: {component} - id {id}: Successfully delete Cell {cell_num}",
                        also_console=True,
                    )
                else:
                    raise Exception(
                        f"Component: {component} - id {id}: Fail to validate delete {cell_num}"
                    )
        except Exception as e:
            raise Exception(
                f"Component: {component} - id {id}: Could not delete CELL {cell_num} due to error: {str(e)}"
            ) from e

    def start_mplane(self, id: str = None) -> None:
        """
        Description:
            Starts the MPlane Binary
        Parameters:
            id: The id of DU object to start MPLANE (Eg. DU1). Otherwise, start MPLANE on all DU objects in yaml
        Returns:
            None
        """
        if id is not None:
            du_object = self.testline.get_component_by_id(id)
            mplane_start_status = du_object.start_mplane()
            if mplane_start_status:
                logger.info(
                    f"====== MPlane binary of DU '{du_object.id}' is started successfully\n",
                    also_console=True,
                )
            else:
                raise FrameworkException(
                    f"MPlane of DU '{du_object.id}' was not started successfully, "
                    "could not find the mplane startup message in logs, exiting."
                )
        else:
            list_du_objects = self.testline.get_components_by_type("DU")
            for du_object in list_du_objects:
                mplane_start_status = du_object.start_mplane()
                if mplane_start_status:
                    logger.info(
                        f"====== MPlane binary of DU '{du_object.id}' is started successfully\n",
                        also_console=True,
                    )
                else:
                    raise FrameworkException(
                        f"MPlane of DU '{du_object.id}' was not started successfully, "
                        "could not find the mplane startup message in logs, exiting."
                    )

    def stop_mplane(self, id : str = None) -> None:
        """
        Description:
            Stops the MPlane Binary
        Parameters:
            id: The id of DU object to stop MPLANE (Eg. DU1). Otherwise, stop MPLANE on all DU objects in yaml
        Returns:
            None
        """
        if id is not None:
            du_object = self.testline.get_component_by_id(id)
            mplane_stop_status = du_object.stop_mplane()
            if mplane_stop_status:
                logger.info(
                    f"====== Mplane binary of DU '{du_object.id}' is stopped successfully\n",
                    also_console=True,
                )
            else:
                raise FrameworkException(
                    f"Mplane binary of DU '{du_object.id}' is not stopped successfully, exiting"
                )
        else:
            list_mplane_stop_failed = []
            list_du_objects = self.testline.get_components_by_type("DU")
            for du_object in list_du_objects:
                try:
                    mplane_stop_status = du_object.stop_mplane()
                    if mplane_stop_status:
                        logger.info(
                            f"====== Mplane binary of DU '{du_object.id}' is stopped successfully\n",
                            also_console=True,
                        )
                    else:
                        list_mplane_stop_failed.append(du_object.id)
                except Exception:
                    list_mplane_stop_failed.append(du_object.id)
                    continue
            if list_mplane_stop_failed:
                raise FrameworkException(
                    f"Failed to stop Mplane binary of DU component(s): {list_mplane_stop_failed}"
                )

    def check_current_components_and_force(self, components: List) -> None:
        """
        Description:
            This function will check component still exist and stop it before run
        Parameters:
            components (List): The list component of objects we want to check.
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        run_mode = BuiltIn().get_variable_value("${RUNMODE}")
        for component in reversed(components):
            component_info = component.type if isinstance(component.id, list) else component.id
            if component.type in ["L1", "RU", "NE", "AtteroX", "ATT"]:
                continue
            elif component.type == "UE" and isinstance(
                component, (AndroidUE, SimnovusUE, KeySightUE, AccuverUE)
            ):
                continue
            if hasattr(component, "status"):
                component_status = component.status()
                logger.debug(f"{component_info}: {component_status}")
                if "running" in component_status or "operational" in component_status:
                    logger.warn(f"Component {component_info} is running!")
                    # Restart ALL components if need.
                    if run_mode == "FORCE":
                        logger.info(
                            f"Component {component_info} will stopped with mode {run_mode}!",
                            also_console=True,
                        )
                        if component.type == "CORE":
                            component.stop(stop_xfe=True)
                        elif component.type == "DU":
                            # TODO this is workaround before ticket MP-38153 done
                            component.stop()
                            # Stop MPLANE
                            if component.mplane_start_script == "start_mplane":
                                component.stop_mplane()
                        else:
                            component.stop()
                        component_status = component.status()
                        if (
                            "running" in component_status
                            or "operational" in component_status
                        ):
                            raise FrameworkException(
                                f"Component {component_info} is still running. Please stop {component_info} by manual before running RATE!"
                            )
                        else:
                            logger.info(
                                f"Component {component_info} is stopped with mode {run_mode} successfully!",
                                also_console=True,
                            )
                    else:
                        logger.warn(
                            "Not automatically stopping already running containers. \
                        Please check other containers are not running or use robot --variable RUNMODE:FORCE"
                        )
                        raise FrameworkException(
                            f"Component {component_info} is running. Please stop {component.type} by manual before running RATE!"
                        )
                else:
                    logger.info(f"Component {component_info} is stopped")
            else:
                raise FrameworkException(
                    f"Component {component_info} NOT support to get status"
                )

    def check_running_components(
        self,
        *components_ids: str,
        restart_components: bool = False,
        collect_logs: bool = True,
        skip_test_on_crash: bool = False,
    ) -> bool:
        """
        Description:
            This method will check if component is running or not and detect core dump in the TL.
        Parameters:
            components_id (List, optional): The list component want to check. if no components passed , it will check over all components.
            restart_components (bool, optional): True if you want to restart ALL components after detecting core dump.
                                                 False if you don't want to restart ALL components. Default to True
            collect_logs(bool, optional): True, by default, to collect logs when the component is not running.
                                          False, not collect the logs but only check the running components
            skip_test_on_crash(bool, optional): True, it will skip the test and move to the next test
                                                False, it will continue test execution and won't skip any keywords
        Return:
            True: if all of components are running, other wise return False.
        """
        logger.info("Checking Running Components", also_console=True, banner=True)
        is_all_component_good = True
        # Support to check with ALL components
        if components_ids:
            self.component_dict = {}
            for id in components_ids:
                component = self.testline.get_component_by_id(id)
                if component.type in self.component_dict:
                    self.component_dict[component.type].append(component)
                else:
                    self.component_dict[component.type] = [component]
        else:
            self.component_dict = self.testline.components_dict
        # Create a list contains list of components objects
        components_list = [
            value for values in self.component_dict.values() for value in values
        ]
        for component in components_list:
            if component.type in ["L1", "RU", "NE", "AtteroX", "ATT"]:
                continue
            logger.info(
                f"====== Checking components {component.type if isinstance(component.id, list) else component.id} are running or not"
            )
            if hasattr(component, "status"):
                ret_status = component.status()
                if "stopped" in ret_status:
                    if collect_logs:
                        logger.error(
                            f"Component {component.type if isinstance(component.id, list) else component.id} is NOT good, collect coredump logs!"
                        )
                        if Keywords.test_case_directory_path:
                            log_directory = Keywords.test_case_directory_path
                        else:
                            log_directory = Keywords.test_suite_directory_path
                        self.log_manager.transfer_logs(components_list, log_directory, copy_coredump="True")
                    else:
                        logger.error(
                            f"Component {component.type if isinstance(component.id, list) else component.id} is NOT good"
                        )
                    # Restart ALL components if need.
                    if restart_components:
                        logger.info(
                            "Restart ALL components to recovery the setup!",
                            also_console=True,
                        )
                        self.restart_components(components_ids)
                    else:
                        logger.warn(
                            "No restart components after detecting binary is stopped!"
                        )
                    is_all_component_good = False
                    break
                elif "crashed" in ret_status:
                    logger.info(
                        f"{component.type if isinstance(component.id,list) else component.id} has crashed!"
                    )
                    if skip_test_on_crash:
                        self.test_case_control.skip(msg="Skipping the test")
                else:
                    logger.info(
                        f"Component {component.type if isinstance(component.id,list) else component.id} is good state"
                    )
            else:
                raise FrameworkException(
                    f"Component {component.type if isinstance(component.id,list) else component.id} NOT support to get status"
                )
        if is_all_component_good:
            logger.info(
                f"All components: {component.type if isinstance(component.id,list) else component.id} are good!",
                also_console=True,
            )
        return is_all_component_good

        # TOOL
    def get_current_alarms(self, component_ids: Optional[List] = []) -> dict:
        """
        Description:
            This function helps to fetch the list of current alarms with their severity from OAM
        Parameters:
            component_ids (List): The list component IDs for which we want to check the current alarms. example values: ["CUCP1", "CUUP1", "DU1"].
                                if no components passed , it will check over all components in testline yaml.
        Returns:
            alarm_dict (dict): The dictionary of current alarms with severity.
        """
        alarm_dict = {}
        component_alarm_dict = {}
        try:
            if component_ids:
                tl_components = [self.testline.get_component_by_id(component) for component in component_ids]
            else:
                tl_components = self.testline.components
            for component in tl_components:
                if component.type not in ["CUCP", "CUUP", "DU"]:
                    logger.info(str(component.type) + " is an unsupported component for getting alarms, skipping...")
                    continue
                else:
                    alarm_severity_cmd = str(
                        Global_Variables.netconf_console_path
                        + "netconf-console"
                        + " --host="
                        + component.oam_ip
                        + " --port="
                        + str(Global_Variables.oam_port)
                        + " --user=netconf --privKeyType=rsa --privKeyFile="
                        + Global_Variables.NETCONF_PRIVATE_KEYPATH
                        + " --get -x ManagedElement/AlarmList/attributes/alarmRecords"
                    )
                    if hasattr(component, "connection"):
                        component_connection: SSHConnection = component.connection
                    else:
                        raise FrameworkException(f"Component {component.id} does not have connection attribute")
                    alarm_output = component_connection.sendCommand(alarm_severity_cmd)
                    python_dict = xmltodict.parse(alarm_output)
                    if 'rpc-reply' in python_dict and 'data' in python_dict['rpc-reply']:
                        if str(python_dict['rpc-reply']['data']) != "None" and 'ManagedElement' in python_dict['rpc-reply']['data'] and 'AlarmList' in python_dict['rpc-reply']['data']['ManagedElement'] and 'alarmRecords' in python_dict['rpc-reply']['data']['ManagedElement']['AlarmList']['attributes']:
                            alarm_records = python_dict['rpc-reply']['data']['ManagedElement']['AlarmList']['attributes']['alarmRecords']
                        else:
                            logger.info("No alarm records were found for component " + str(component.id), also_console=True)
                            continue
                        for alarm_record in alarm_records:
                            alarm_name = alarm_record['dvsAlarmData']['alarmName']
                            alarm_severity = alarm_record['perceivedSeverity']

                            keys = ['CRITICAL', 'WARNING', 'MAJOR', 'CLEARED']
                            component_alarm_dict = {key: set() for key in keys}
                            if alarm_severity in keys :
                                component_alarm_dict[alarm_severity].add(alarm_name)
                        logger.info(f"=== The alarm for {component.id} with severity ===", also_console=True)
                        logger.info(component_alarm_dict, also_console=True)
                    else:
                        logger.info("No alarm records were found for component " + str(component.id), also_console=True)

                alarm_dict[component.id] = component_alarm_dict
                logger.info("=== The alarms for each component with severity ===", also_console=True)
                logger.info(alarm_dict, also_console=True)
            return alarm_dict

        except Exception as e:
            logger.error(f"Cannot get the alarms successfully due to {e}")
            raise FrameworkException() from e

    def check_operational_components(self, components: List = [], check_all_operational: bool = False) -> tuple[bool, list, list]:
        """
        Description:
            This function will check operational state of components in list.
        Parameters:
            components(List): The list component of objects we want to check.
            check_all_operational (bool): Checks if all components are operational
        Returns:
            operational_components(Bool): True if all components are in operational state, otherwise return False.
            running_components(List): The list of running components after check.
            not_operational_components(List): The list of not operational/running components after check.
        """
        logger.info("Checking Operational Components", also_console=True, banner=True)
        operational_components = []
        not_operational_components = []
        running_components = []
        if components:
            tl_components = [self.testline.get_component_by_id(component) for component in components]
        else:
            tl_components = self.testline.components
        for component in reversed(tl_components):
            if component.type == "UE" and isinstance(
                component, (AndroidUE, SimnovusUE, KeySightUE, AccuverUE)
            ):
                continue
            if hasattr(component, "status"):
                if component.type == "RU" and "GenericRU" in type(component).__name__:
                    component_status = component.status(return_status=True)
                else:
                    component_status = component.status()
                logger.debug(f"{component.id}: {component_status}")
                if OperationalStatus.OPERATIONAL.value in component_status:
                    logger.info(f"Component {component.type if isinstance(component.id, list) else component.id} is in operational state!", also_console=True)
                    operational_components.append(True)
                elif component.type in ['CORE', 'RU', 'UE'] and OperationalStatus.RUNNING.value in component_status:
                    operational_components.append(True)
                    logger.info(f"Component {component.type if isinstance(component.id, list) else component.id} is running!")
                else:
                    not_operational_components.append(component.type if isinstance(component.id, list) else component.id)
                    operational_components.append(False)

                if OperationalStatus.RUNNING.value in component_status or OperationalStatus.OPERATIONAL.value in component_status:
                    running_components.append(component)
            else:
                logger.error(
                    f"Component {component.type if isinstance(component.id, list) else component.id} NOT support to get status"
                )
        if check_all_operational:
            logger.info("Checking if all components are operational", also_console=True, banner=True)
            if all(operational_components):
                logger.info("===== All components are operational!",
                            also_console=True
                            )
            else:
                raise FrameworkException(
                    f"===== Some components are not operational {not_operational_components} are not operational"
                )
        return all(operational_components), running_components, not_operational_components

    def test_line_start(
        self,
        num_cells: int = 1,
        components_ids: List = None,
        start_config: bool = True,
        check_cell_up: bool = True,
        skip_validation: bool = False,
    ) -> None:
        """
        Description:
            This function will start all the components of the test line
        Parameters:
            num_cells: Number of DU cells to bring up
            components_ids (list): To start certain components, by default all components will be started.
            start_config (bool): False if we don't want to configure for the gNB components, default is True.
            check_cell_up (bool): to know if the core components has started or not, because the DU starting message differs according to whether the 5gcore is up or not.
            skip_validation (bool): True if we don't want to validate operational state of gNB components, default is False.
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        logger.info("Starting the Test Line", also_console=True, banner=True)
        if components_ids:
            tl_components = [self.testline.get_component_by_id(component) for component in components_ids]
        else:
            tl_components = self.testline.components

        self.list_components_id_started = []
        Keywords.list_components_id_started = []
        components_are_operational = False

        try:
            # Arrange list components: OAMA first, UE last as a workaround for bugs MP-87361 and MP-87566
            # TODO: Below codes need to be removed when MP-87361 and MP-87566 solved
            components = [component for component in tl_components if component.type == "OAMA"]
            for component in tl_components:
                if component.type not in ["OAMA", "UE"]:
                    components.append(component)
            tl_components = [component for component in tl_components if component not in components]
            components.extend(tl_components)

            # Check if all components are running:
            component_statuses = {
                component.id[0] if isinstance(component.id, list) else component.id: component.status() for component in components
            }
            # TODO: Need to be uncomment after MP-72343 unblocked with its dependency MP-88807 solved
            # if all(status in [OperationalStatus.RUNNING.value, OperationalStatus.OPERATIONAL.value] for status in component_statuses.values()):
            #     logger.info(
            #         "All components are in operational or running state! Skipping starting components",
            #         also_console=True,
            #     )
            # TODO: Remove below codes after MP-83576: NF reconnected support done
            if all(status == OperationalStatus.OPERATIONAL.value for status in component_statuses.values()):
                logger.info(
                    "====== All components are in operational state! Skipping starting components",
                    also_console=True,
                )
                components_are_operational = True
            # Start non-running components
            else:
                # TODO: Remove below codes after MP-72343 unblocked with its dependency MP-88807 solved
                logger.info(
                    "====== All components are NOT in operational state! Stop previously running components then start all.",
                    also_console=True,
                )
                for component in components:
                    id = component.id[0] if isinstance(component.id, list) else component.id
                    if component_statuses[id] in [OperationalStatus.RUNNING.value, OperationalStatus.OPERATIONAL.value]:
                        component.stop()

                # TODO: Need to be uncomment after MP-72343 unblocked with its dependency MP-88807 solved and 2 bugs MP-87566, MP-87361 solved
                # for component in components:
                #     id = component.id[0] if isinstance(component.id, list) else component.id
                #     if component_statuses[id] not in [OperationalStatus.RUNNING.value, OperationalStatus.OPERATIONAL.value]:
                #         logger.info(
                #             f"Starting {component.type if isinstance(component.id, list) else component.id}",
                #             also_console=True, banner=True, banner_width=40
                #         )
                #         self.list_components_id_started.append(id)
                #         self.get_gnb_version(components_ids=[id])
                #         component.start()

                # TODO: Remove below codes after MP-72343 unblocked with its dependency MP-88807 solved
                for component in components:
                    id = component.id[0] if isinstance(component.id, list) else component.id
                    logger.info(
                        f"Starting {component.type if isinstance(component.id, list) else component.id}",
                        also_console=True, banner=True, banner_width=40
                    )
                    Keywords.list_components_id_started.append(id)
                    self.get_gnb_version(components_ids=[id])
                    component.start()

                # Check for all components to reach running state
                testline_running = False
                logger.info(
                    "Checking all components are operational or running", also_console=True, banner=True, banner_width=40
                )
                testline_running, component_statuses = utils.poll_status_for_components(components=components,
                                                                                        timeout=Global_Variables.COMPONENT_START_TIMEOUT,
                                                                                        desired_states=[OperationalStatus.RUNNING.value, OperationalStatus.OPERATIONAL.value]
                                                                                        )
                if not testline_running:
                    comp_start_failed = {}
                    for comp_id, comp_status in component_statuses.items():
                        if comp_status not in [OperationalStatus.RUNNING.value, OperationalStatus.OPERATIONAL.value]:
                            comp_start_failed[comp_id] = comp_status
                    raise ComponentStartFailed(
                        "All components failed to reach running state! "
                        f"Component started failed and its status: {comp_start_failed}"
                    )

            # Check for all OAMA components to reach NF_READY state
            oama_nf_ready = False
            timeout_time = time.time() + Global_Variables.NF_READY_TIMEOUT
            logger.info(
                "Checking OAMA components netconf state", also_console=True, banner=True, banner_width=40
            )
            oama_components = [component for component in components if component.type == "OAMA"]
            while time.time() < timeout_time:
                oama_states = {
                    oama.id: utils.get_netconf_state_for_oama(oama) for oama in oama_components
                }
                if all(oama_state == OamaState.NF_READY for oama_state in oama_states.values()):
                    oama_nf_ready = True
                    logger.info(f"OAMA components reach {OamaState.NF_READY}", also_console=True)
                    break
            if not oama_nf_ready:
                raise ComponentStartFailed(
                    f"OAMA components failed to reach {OamaState.NF_READY} state after {Global_Variables.NF_READY_TIMEOUT}!"
                )

            # Configure all components
            if not start_config or components_are_operational:
                logger.info(
                    "Skipping configuring components", also_console=True, banner=True, banner_width=40
                )
            else:
                for component in components:
                    logger.info(
                        f"Configuring {component.type if isinstance(component.id, list) else component.id}",
                        also_console=True, banner=True, banner_width=40
                    )
                    component.start_config()

                # Check for all components to reach operational state
                if not skip_validation:
                    logger.info(
                        "Checking all components are operational", also_console=True, banner=True, banner_width=40
                    )
                    testline_operational, component_statuses = utils.poll_status_for_components(components=components,
                                                                                                timeout=Global_Variables.COMPONENT_OPERATIONAL_TIMEOUT,
                                                                                                desired_states=[OperationalStatus.OPERATIONAL.value]
                                                                                                )
                    if not testline_operational:
                        comp_start_failed = {}
                        for comp_id, comp_status in component_statuses.items():
                            if comp_status != OperationalStatus.OPERATIONAL.value:
                                comp_start_failed[comp_id] = comp_status
                        raise ComponentStartFailed(
                            "All components failed to reach operational state! "
                            f"Component started failed and its status: {comp_start_failed}"
                        )
                else:
                    logger.info(
                        "Skipping checking components operational", also_console=True, banner=True, banner_width=40
                    )

        except Exception as e:
            BuiltIn().set_suite_variable("${SKIP_TEST}", "True")
            logger.error(
                f"====== Test Line start failed due to : {str(e)}"
            )
            # collect logs when failed in test line start
            # In Suite Teardown, the log will be collected to test suite directory
            if BuiltIn().get_variable_value("${SUITE_STATUS}") is not None:
                directory = Keywords.test_suite_directory_path
            else:
                if Keywords.test_case_directory_path is None:
                    directory = Keywords.test_suite_directory_path
                else:
                    directory = Keywords.test_case_directory_path
            component_objects = Keywords.get_list_started_components()
            log_directory = os.path.join(directory, "Logs_TL_start_failed")
            self.log_manager.create_test_case_directory_structure(str(log_directory), component_objects, Global_Variables.COMPONENTS_SUBFOLDERS)
            self.log_manager.transfer_logs(component_objects, log_directory, copy_coredump="True")
            raise FrameworkException(
                f"====== Test Line start failed due to : {str(e)}"
            ) from e

    def test_line_stop(self, components_ids: List = None) -> None:
        """
        Description:
            This function will stop all the components of the test line. If xfe doesn't need to be stopped, use "CORE_WITHOUT_XFE
        Parameters:
            components_ids (List): stop certain components, by default all components will be stopped. If "L1" needs to be stopped
            for some reason, explicitly list all components including L1.
        Returns:
            None
        Example:
            Test Line Stop
            Test Line Stop    components=['CUCP1','CUUP1','DU2', 'UE1', 'MinervaL1']
        """
        try:
            logger.info(
                "Stopping Test Line", also_console=True, banner=True
                )
            if components_ids is None:
                components = self.testline.components
            else:
                components = [self.testline.get_component_by_id(component) for component in components_ids]

            stop_comp_threads = []
            thread_instance = logger()
            thread_instance.start_thread_logging()

            for component in components:
                component_id = component.id[0] if isinstance(component.id, list) else component.id
                stop_comp_thread = threading.Thread(
                                target=utils.safe_thread_execution,
                                args=(component.stop,),
                                name=component_id
                                )
                stop_comp_thread.start()
                stop_comp_threads.append(stop_comp_thread)

                if component_id in Keywords.list_components_id_started:
                    Keywords.list_components_id_started.remove(component_id)

            for stop_thread in stop_comp_threads:
                stop_thread.join()

            thread_instance.stop_thread_logging(stop_comp_threads)

        except Exception as exc:
            raise ComponentStopFailed(f"Components failed to stop due to {exc}")

    def trigger_ri(self, cell_id: int, dir: str, ri: int, id: str = None) -> None:
        """
        Description:
            This function will trigger Rank Index
        Parameters:
            cell_id (int): The cell ID
            dir (str): The direction of traffic
            ri (int): The RI value, allowed values 1-4, if value is outside this range "Parse Ri/Beam Fail, value out of range" message
            pops up in UESIM console
            id (str): The UE ID
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        # This keyword use for UE simulation
        if id is not None:
            ue = self.testline.get_component_by_id(id)
        else:
            logger.info(
                "====== No component id provided. So, The function trigger_ri will be running on the first UE"
            )
            ue = self.testline.get_components_by_type("UE")[0]
            id = ue.id[0]
        is_ri_triggered = ue.trigger_ri(cell_id, dir, ri, id)
        if is_ri_triggered:
            if int(ri) > 4 or int(ri) < 1:
                logger.info(
                    f"The RI with value {ri} was not triggered successfully on the UE ID: {id} "
                    f"because the RI index was out of range (1-4)\n",
                    also_console=True,
                )
            else:
                logger.info(
                    f"The RI with value {ri} was successfully triggered on the UE ID: {id}\n",
                    also_console=True,
                )
        else:
            raise Exception(
                "\n The RI was not triggered successfully. Please check for errors.\n"
            )

    def trigger_cqi(
        self,
        cell_id: int,
        dir: str,
        cqi: int,
        ullacqi: int = None,
        avgsnr: int = None,
        id: str = None,
    ) -> None:
        """
        Description:
            This function will trigger cqi
        Parameters:
            cell_id (int): The cell ID
            dir (str): The direction of traffic
            cqi (int): The CQI value
            ullacqi (int): The link adaptation CQI
            avgsnr (int): The SNR
            id (str): The UE ID
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        if id is not None:
            ue = self.testline.get_component_by_id(id)
        else:
            logger.info(
                "====== No component id provided. So, The function trigger_cqi will be running on the first UE"
            )
            ue = self.testline.get_components_by_type("UE")[0]
            id = ue.id[0]
        if dir == "1":
            if ullacqi is not None and avgsnr is not None:
                logger.console(
                    f"\nSending command to trigger CQI on Cell ID {cell_id} UE ID {id} with cqi "
                    f"{cqi}, ullacqi {ullacqi} and avgsnr {avgsnr} in the DL direction ..."
                )
                raise Exception(
                    "The parameters ullacqi and avgsnr are not allowed for the DL direction,exiting."
                )

            elif ullacqi is not None:
                logger.console(
                    f"\nSending command to trigger CQI on Cell ID {cell_id} UE ID {id} with cqi "
                    f"{cqi} and ullacqi {ullacqi} in the DL direction ..."
                )
                raise Exception(
                    "The parameter ullacqi is not allowed for the DL direction,exiting."
                )

            elif avgsnr is not None:
                logger.console(
                    f"\nSending command to trigger CQI on Cell ID {cell_id} UE ID {id} with cqi "
                    f"{cqi} and avgsnr {avgsnr} in the DL direction ..."
                )
                raise Exception(
                    "The parameter avgsnr is not allowed for the DL direction,exiting."
                )

        is_cqi_triggered = ue.trigger_cqi(cell_id, dir, cqi, ullacqi, avgsnr, id)

        if is_cqi_triggered:
            logger.info(
                f"The CQI with value {cqi} was successfully triggered on the UE ID :{id}",
                also_console=True,
            )
        else:
            raise Exception(
                "\n The CQI was not triggered successfully. Please check for errors."
            )

    def ue_attach(
        self,
        id: str,
        cell_id: int = 1,
        est_cause: str = "MO_SIGNALLING",
        scenario: str = "0",
        nia: str = "{0,1,2,3}",
        nea: str = "{0,1,2,3}",
        dnn: str = None,
        expect_failure: bool = False,
        timeout: int = 120,
        packet_capture: str = "None",
        with_ue_capability: bool = False,
        background_ping_enabled: bool = True,
    ) -> None:
        """
        Description:
            This function will attach ue
        Parameters:
            id (str): The user equipment id to be attached to the network
            cell_id (int): The cell ID to attach the UE to the network with default value 1
            est_cause (int): represents establishment cause for the call it's set to 3 by default
            scenario (str): represents the scenario and it's set to 0 by default which means no scenario
            The scenarios are:
                0 = NO_SCENARIO
                1 = REESTAB_PST_RECFG
                2 = SEND_RRC_SETUP_COMP_TWICE
                4 = SEND_RRC_SEC_MODE_FAILURE
                8 = INVALID_PLMN
            nea (str): represents new radio encryption algorithm
            nia (str): represents new radio integrity algorithm
            dnn (str): represents the DNN value for multi PDU session
            timeout (int): timeout
            expect_failure (bool): represents expected result for attaching UE
            packet_capture (str): Config to enable packet capture at UE (NONE, RRC, MAC, SIB, MIB, DATA)
            with_ue_capability (bool): indicates whether using ue capability config for ue or not. The keyword prepare_ue_capability_file must be executed in advance if this flag is set to True
            background_ping_enabled (bool): indicates whether to start a ping process on the UE after attach to prevent an inactivity timeout. Currently only supported on podman and android UEs.
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        logger.info(f"Attaching UE: {id}", also_console=True, banner=True)
        UE = self.testline.get_component_by_id(id)
        if UE:
            UE.attach(
                id,
                cell_id,
                est_cause,
                scenario,
                nia,
                nea,
                dnn,
                expect_failure=expect_failure,
                timeout=timeout,
                packet_capture=packet_capture,
                with_ue_capability=with_ue_capability,
                background_ping_enabled=background_ping_enabled
            )
            if UE.state != State.Attached.value:
                raise Exception(
                    "CELL:UE {}:{} attach failed, exiting".format(id, cell_id)
                )
        else:
            raise Exception("UE {} doesn't exist".format(id))

    def start_video_on_youtube_for_E2E_Lab(self, video_link: str, HQ_Video: bool = True, id: str = None) -> None:
        """
        Description:
            This function will trigger to start video on youtube for E2E LAB
        Parameter:
            video_link (str): link video to watch
            HQ_Video (bool):  If True, play video on high quality
            id:               The id of UE object to start video (Eg. UE1). Otherwise, start on the first UE in yaml

        Returns:
            None: This function only executes the codes and does not return any value.
        """
        if id is not None:
            logger.info(
                f"====== Starting Video on Youtube on UE {id}...", also_console=True
            )
            ue_object = self.testline.get_component_by_id(id)
        else:
            logger.info(
                "====== No component id provided, starting Video on Youtube on the first UE...",
                also_console=True,
            )
            ue_object = self.testline.get_components_by_type("UE")[0]
        ue_object.start_video_on_youtube_for_E2E_Lab(video_link, HQ_Video=HQ_Video)

    def pause_video_on_youtube_and_close_browser_for_E2E_Lab(self, id: str = None) -> None:
        """
        Description:
            This function will trigger to pause video on youtube and will close current session of browser for E2E LAB
        Parameters:
            id:               The id of UE object to pause video (Eg. UE1). Otherwise, pause on the first UE in yaml

        Returns:
            None: This function only executes the codes and does not return any value.
        """
        if id is not None:
            logger.info(
                f"====== Pausing Video on Youtube on UE {id}...", also_console=True
            )
            ue_object = self.testline.get_component_by_id(id)
        else:
            logger.info(
                "====== No component id provided, pausing Video on Youtube on the first UE...",
                also_console=True,
            )
            ue_object = self.testline.get_components_by_type("UE")[0]
        ue_object.pause_video_on_youtube_and_close_browser_for_E2E_Lab()

    def start_zoom_call_for_E2E_Lab(self, id: str = None) -> None:
        """
        Description:
            This function will trigger the browser to start zoom call.
        Parameter:
            id: The id of UE object to start zoom call (Eg. UE1). Otherwise, start on the first UE in yaml
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        if id is not None:
            logger.info(f"====== Starting Zoom call on UE {id}...", also_console=True)
            ue_object = self.testline.get_component_by_id(id)
        else:
            logger.info(
                "====== No component id provided, starting Zoom call on the first UE...",
                also_console=True,
            )
            ue_object = self.testline.get_components_by_type("UE")[0]
        ue_object.start_zoom_call_for_E2E_Lab()

    def stop_zoom_meeting_for_E2E_Lab(self, id: str = None) -> None:
        """
        Description:
            This function will trigger the browser to stop zoom call.
        Parameter:
            id: The id of UE object to stop zoom call (Eg. UE1). Otherwise, stop on the first UE in yaml
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        if id is not None:
            logger.info(f"====== Stopping Zoom call on UE {id}...", also_console=True)
            ue_object = self.testline.get_component_by_id(id)
        else:
            logger.info(
                "====== No component id provided, stopping Zoom call on the first UE...",
                also_console=True,
            )
            ue_object = self.testline.get_components_by_type("UE")[0]
        ue_object.stop_zoom_meeting_for_E2E_Lab()

    def ftp_download(
        self,
        ftp_server_name: str,
        folder_name: str = None,
        file_name: str = None,
        transfer_timeout_seconds: int = 20,
        id: str = None,
    ) -> None:
        """
        Description:
            This function will download a file to the UE using the application AndFTP
        Parameters:
            ftp_server_name:            The name of an ftp server that is already configured on AndFTP
            folder_name:                The folder containing the file to be transferred.
            file_name:                  The name of the file to be transferred
            transfer_timeout_seconds:   The maximum number of seconds to wait for an FTP transfer
                                        to complete
            id:                         The id of UE object to dowload a file to (Eg. UE1).
                                        Otherwise, download to the first UE in yaml
        Pre-requisites:
            The AndFTP application is installed.
            The FTP server that is specified by the parameter ftp_server_name is configured.
            The FTP server configuration contains the following:
            - username/password (if the FTP server requires this)
            - remote directory
        Returns:
            None: This function does not return any value.
        """
        if id is not None:
            logger.info(
                f"====== Starting FTP download to UE {id}...", also_console=True
            )
            ue_object = self.testline.get_component_by_id(id)
        else:
            logger.info(
                "====== No component id provided, starting FTP download for the first UE...",
                also_console=True,
            )
            ue_object = self.testline.get_components_by_type("UE")[0]
        ue_object.ftp_download(
            ftp_server_name, folder_name, file_name, transfer_timeout_seconds
        )

    def ftp_upload(
        self,
        ftp_server_name: str,
        folder_name : str = None,
        file_name: str = None,
        transfer_timeout_seconds: int = 20,
        id: str = None,
    ) -> None:
        """
        Description:
            This function will upload a file to the UE using the application AndFTP
        Parameters:
            ftp_server_name:            The name of an ftp server that is already configured on AndFTP
            folder_name:                The folder containing the file to be transferred.
            file_name:                  The name of the file to be transferred
            transfer_timeout_seconds:   The maximum number of seconds to wait for an FTP transfer
                                        to complete
            id:                         The id of UE object to upload a file to (Eg. UE1).
                                        Otherwise, upload to the first UE in yaml
        Pre-requisites:
            The AndFTP application is installed.
            The FTP server that is specified by the parameter ftp_server_name is configured.
            The FTP server configuration contains the following:
            - username/password (if the FTP server requires this)
            - remote directory
        Returns:
            None: This function does not return any value.
        """
        if id is not None:
            logger.info(f"====== Starting FTP upload to UE {id}...", also_console=True)
            ue_object = self.testline.get_component_by_id(id)
        else:
            logger.info(
                "====== No component id provided, starting FTP upload for the first UE...",
                also_console=True,
            )
            ue_object = self.testline.get_components_by_type("UE")[0]
        ue_object.ftp_upload(
            ftp_server_name, folder_name, file_name, transfer_timeout_seconds
        )

    def trigger_session_request(self, dnn: str, id: str = None) -> str:
        """
        Description:
            This function will trigger a new PDU session with the provided DNN and UE to the corresponding Cell in the network
        Parameters:
            dnn (str): The data network name to trigger a session request
            id (str): The UE ID which the session will be triggered
        Returns:
            pdu_session_num (str): The pdu session number
            pdu_session_ip (str): The pdu session ip
        Example:
            ${pdu_ip_gsm}    ${pdu_session_gsm}=    Trigger Session Request    ue_id=1    dnn=GSM
        """
        if id is not None:
            ue = self.testline.get_component_by_id(id)
        else:
            logger.info(
                "====== No component id provided. So, The function trigger_session_request will be running on the first UE"
            )
            ue = self.testline.get_components_by_type("UE")[0]
            id = ue.id[0]
        pdu_session_num, pdu_session_ip = ue.trigger_session_request(dnn, id)
        if pdu_session_num is None:
            raise Exception(
                f"PDU Session Num for DNN: {dnn} is not retrieved successfully, exiting!\n"
            )
        if pdu_session_ip is None:
            raise Exception(
                f"PDU Session IP for DNN: {dnn} is not retrieved successfully, exiting!\n"
            )
        return pdu_session_ip, pdu_session_num

    def trigger_session_release_request(self, pdu_session_num: str, id: str = None) -> bool:
        """
        Description:
            This function will trigger a PDU session release request
        Parameters:
            pdu_session_num (str): PDU session number; PDU session at the UE and network
            id (str): The user equipment id to be attached to the network
        Returns:
            is_session_released (bool)
                True if  session release request triggered
                False if session release request is not triggered
        Example:
            Trigger Session Release Request    pdu_session_num=${pdu_session_gsm}    id=UE1
        ** ${pdu_session_gsm} is return by keyword trigger_session_release_requet **
        """
        if id is not None:
            ue = self.testline.get_component_by_id(id)
        else:
            logger.info(
                "====== No component id provided. So, The function trigger_session_release_request will be running on the first UE"
            )
            ue = self.testline.get_components_by_type("UE")[0]
            id = ue.id[0]
        is_session_released = ue.trigger_session_release_request(pdu_session_num, id)
        if is_session_released:
            logger.info(
                f"====== Trigger session release request for PDU Session Number {pdu_session_num} done "
                "successfully\n",
                also_console=True,
            )
        else:
            raise Exception(
                f"====== Trigger session release request for PDU Session Number {pdu_session_num} "
                f"failed, exiting!\n"
            )

    def config_re_establishment(
        self,
        ids: list = None,
        crnti: Optional[int] = None,
        pci: Optional[int] = None,
        short_mac: Optional[str] = None,
        cause: Optional[int] = None,
        target_cell_id: Optional[int] = None,
        arfcn_dl: Optional[int] = None,
        re_estab_other_cell: Optional[int] = None,
        validate: bool = True,
    ) -> bool:
        """
        Description:
            Configure RRC reestablishment request with the needed scenario
        Parameters:
            ids (list): The UE ID which will initiate the RRC reestablishment
            crnti (int): Unique UE identification which is a positive integer used as an identifier of the RRC Connection
            pci (int): Unique positive integer value for identifying cells, a value between 0 and 1007.
            short_mac(str): Used to identify and verify the UE at RRC connection re-establishment. It's set to 0 by default
            cause (int): Cause for the RRC reestablishment
            The causes are:
                            0 = Reconfiguration failure
                            1 = Handover failure
                            2 = Other failure
            target_cell_id (int): The value of PCI to which UE has to be reestablished.
            arfcn_dl(int): The DL arfcn of target cell
            re_estab_other_cell(int): to trigger reestablishment on other cell(default set to None).
            validate(bool) : Default set to True, when changed to False reduces execution time of keyword,
                            by not validating results of keyword and nothing will be printed on console

        Returns:
            re_establishment_configured (bool):  True if configuration is done
                                                 False if configuration failed
        """
        logger.info("Configuring RRC Re-establishment Request", also_console=True, banner=True)
        if ids is None:
            ue = self.testline.get_components_by_type("UE")[0]
            logger.info(
                "====== No component id provided. So, The function config_re_establishment will be running for multiple UE"
            )
            ids = ue.id
        for id in ids:
            ue = self.testline.get_component_by_id(id)
            re_establishment_configured = ue.config_re_establishment(
                id, crnti, pci, short_mac, cause, target_cell_id, arfcn_dl, re_estab_other_cell, validate
            )
            if validate:
                if re_establishment_configured:
                    logger.info(
                        f"====== Configure RRC reestablishment request for UE ID {id} is done successfully\n",
                        also_console=True,
                    )
                else:
                    raise Exception(
                        "====== Configure RRC reestablishment request failed\n"
                    )

    def trigger_re_establishment(self, ids: list = None, other_cell: bool = False, validate: bool = True) -> bool:
        """
        Description:
            Trigger RRC Re establishment request from the UESIM based on the configuration done. Applicable for UE in connected state only
        Parameters:
            ids (list): The UE ID which will initiate the RRC reestablishment
            other_cell(bool) : Default set to false, can be set to True when trigerring RRE on different cell
            validate(bool) : Default set to True, when changed to False reduces execution time of keyword,
                            by not validating results of keyword and nothing will be printed on console

        Returns:
            re_establishment_triggered (bool):  True if reestablishment is triggered
                                                False if reestablishment is not triggered
        """
        logger.info("Triggering RRC Re-establishment Request", also_console=True, banner=True)
        if ids is None:
            ue = self.testline.get_components_by_type("UE")[0]
            logger.info(
                "====== No component id provided. So, The function config_re_establishment will be running for multiple UE"
            )
            ids = ue.id
        for id in ids:
            ue = self.testline.get_component_by_id(id)
            re_establishment_triggered = ue.trigger_re_establishment(id, other_cell, validate)
            if validate:
                if re_establishment_triggered:
                    logger.info(
                        f"====== Trigger RRC reestablishment request for UE ID {id} is done successfully\n",
                        also_console=True,
                    )
                else:
                    raise Exception(
                        f"====== Configure RRC reestablishment request for UE ID {id} failed\n"
                    )

    def attach_ue_packet_capture(self, cell_id: str, packet_type: str, id: str = None):
        """
        Description:
            This function will attach UE in single cell & packet capture provided UE to the corresponding cell_id in the network and enabled at UE for a specific protocol layer
        Parameters:
            cell_id (int): The cell ID to attach the UE to the network.
            packet_type (str): This argument will triggers the packet capture on the UE side (RRC, SIB, MIB, MAC)
            id (str): The user equipment id to be attached to the network. The id of UE object. Ex: UE1.
        Example:
            Attach UE Packet Capture    1    RRC,MAC,SIB,MIB    UE1
        """
        if id is not None:
            UE = self.testline.get_component_by_id(id)
        else:
            UE = self.testline.get_components_by_type("UE")[0]
            if type(UE.id) is list:
                id = UE.id[0]
            else:
                id = UE.id
        UE.packet_capture(cell_id, id, packet_type)

    def trigger_bler(self, cell_id: int, dir: int, bler: int, id: str = None):
        """
        Description:
            This function will send the trigger bler command using the telnet connection and return the response of the request
        Parameters:
            cell_id (int): The cell ID to attach the UE to the network.
            dir (int): direction (Downlink=1 & Uplink = 0)
            bler (int): bler value in percentage
            id (str): The user equipment id to be attached to the network.
        Example:
            TRIGGER BLER    1   5   1   10
        """
        if id is not None:
            ue = self.testline.get_component_by_id(id)
        else:
            logger.info(
                "====== No component id provided. So, The function trigger_bler will be running on the first UE"
            )
            ue = self.testline.get_components_by_type("UE")[0]
            id = ue.id[0]
        triggered_bler = ue.trigger_bler(cell_id, dir, bler, id)
        if triggered_bler:
            logger.info(
                f"====== UE ID: '{id}' successfully triggered bler with value {bler}",
                also_console=True,
            )
        else:
            raise Exception(f"UE ID: {id} was not attached successfully\n")

    def trigger_ul_sync_loss(self, trig_type: int, id: str = None):
        """
        Description:
            This function will send the trigger a UL sync loss
        Parameters:
            trig_type (int): To trigger an event when the current depth of the queue goes from 0 - 1
            id (str): The user equipment id to be attached to the network.
        """
        if id is not None:
            ue = self.testline.get_component_by_id(id)
        else:
            logger.info(
                "====== No component id provided. So, The function trigger_ul_sync_loss will be running on the first UE"
            )
            ue = self.testline.get_components_by_type("UE")[0]
            id = ue.id[0]
        triggered_ul_sync_loss = ue.trigger_ul_sync_loss(trig_type, id)
        if triggered_ul_sync_loss:
            logger.info(
                f"====== Triggered UL Sync Loss for UE ID:{id} Successfully",
                also_console=True,
            )
        else:
            raise Exception(f"Failed to trigger UL sync loss for UE ID:{id}\n")

    def multiple_ues_attach_one_cell(
        self,
        cell_id: int,
        ue_ids: list,
        est_cause: str = "MO_SIGNALLING",
        scenario: str = "0",
        nia: str = "{0,1,2,3}",
        nea: str = "{0,1,2,3}",
        dnn: str = None,
        expect_failure: bool = False,
        packet_capture: str = "None",
        with_ue_capability: bool = False,
    ) -> None:
        """
        Description:
            This function will attach multiple ues to the single cell
        Parameters:
            cell_id (int): The cell ID will be attached to
            ue_ids (list): The list of start_ue and stop_ue want to attach. Ex: ue_ids: [1,5] -> UE ID: 1,2,3,4,5
            est_cause(str): Default value is "MO_SIGNALLING"
            scenario (str): represents the scenario and it's set to 0 by default.
            The scenarios are:
                0 = NO_SCENARIO
                1 = REESTAB_PST_RECFG
                2 = SEND_RRC_SETUP_COMP_TWICE
                4 = SEND_RRC_SEC_MODE_FAILURE
                8 = INVALID_PLMN
            nia (str): represents new radio integrity algorithm
            nea (str): represents new radio encryption algorithm
            dnn (str): represents the DNN value for multi PDU session
            expect_failure (bool): represents expected result for attaching UE
            packet_capture (str): Config to enable packet capture at UE (NONE, RRC, MAC, SIB, MIB, DATA)
            with_ue_capability (bool): indicates whether using ue capability config for ue or not. The keyword prepare_ue_capability_file must be executed in advance if this flag is set to True
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        logger.info("Attaching UEs to One Cell", also_console=True, banner=True)
        start_ue_id = ue_ids[0]
        stop_ue_id = ue_ids[1]
        for ue_id in range(start_ue_id, stop_ue_id + 1):
            ue = self.testline.get_component_by_id(f"UE{ue_id}")
            ue.attach(
                f"UE{ue_id}",
                cell_id,
                est_cause,
                scenario,
                nia,
                nea,
                dnn,
                expect_failure=expect_failure,
                packet_capture=packet_capture,
                with_ue_capability=with_ue_capability,
            )
            if ue.state != State.Attached.value:
                raise Exception(
                    "CELL:UE {}:{} attach failed, exiting".format(cell_id, ue_id)
                )

    def multiple_ues_attach_multiple_cells(
        self,
        cells_and_ues: dict[int, list[int]],
        est_cause: str = "MO_SIGNALLING",
        scenario: str = "0",
        nia: str = "{0,1,2,3}",
        nea: str = "{0,1,2,3}",
        dnn: Optional[str] = None,
        expect_failure: bool = False,
        packet_capture: str = "None",
        with_ue_capability: bool = False,
    ) -> None:
        """
        Description:
            This function will attach multiple ues to the multiple cells
        Parameters:
            cells_and_ues (dict): The dictionary containt cell ID and UE ID
            Ex: cells_and_ues: {1: [1,3], 2: [4,6]}
                -> attach UE ID = 1,2,3 to CELL ID = 1
                -> attach UE ID = 4,5,6 to CELL ID = 2
            scenario (str): represents the scenario and it's set to 0 by default.
            The scenarios are:
                0 = NO_SCENARIO
                1 = REESTAB_PST_RECFG
                2 = SEND_RRC_SETUP_COMP_TWICE
                4 = SEND_RRC_SEC_MODE_FAILURE
                8 = INVALID_PLMN
            ue_ids (list): The list of start_ue and stop_ue want to attach. Ex: ue_ids: [1,5] -> UE ID: 1,2,3,4,5
            scenario (str): represents the scenario and it's set to 0 by default.
            The scenarios are:
                0 = NO_SCENARIO
                1 = REESTAB_PST_RECFG
                2 = SEND_RRC_SETUP_COMP_TWICE
                4 = SEND_RRC_SEC_MODE_FAILURE
                8 = INVALID_PLMN
            nea (str): represents new radio encryption algorithm
            nia (str): represents new radio integrity algorithm
            dnn (str): represents the DNN value for multi PDU session
            expect_failure (bool): represents expected result for attaching UE
            packet_capture (str): Config to enable packet capture at UE (NONE, RRC, MAC, SIB, MIB, DATA)
            with_ue_capability (bool): indicates whether using ue capability config for ue or not. The keyword
                prepare_ue_capability_file must be executed in advance if this flag is set to True.
        Returns: None
        """
        logger.info("Attaching UEs to Multiple Cells", also_console=True, banner=True)
        for cell_id, ue_range in cells_and_ues.items():
            low, high = ue_range
            for ue_id in range(low, high + 1):
                logger.info(
                    f"Attaching UE ID: {ue_id} to CELL ID: {cell_id}", also_console=True
                )
                ue_id = f"UE{ue_id}"
                ue = self.testline.get_component_by_id(ue_id)
                ue.attach(
                    ue_id,
                    cell_id,
                    est_cause,
                    scenario,
                    nia,
                    nea,
                    dnn,
                    expect_failure=expect_failure,
                    packet_capture=packet_capture,
                    with_ue_capability=with_ue_capability,
                )

                if ue.state != State.Attached.value:
                    raise Exception(
                        f"CELL: {cell_id} UE:{ue_id} attach failed, exiting."
                    )

    def ue_detach(self, id: str, cell_id: int = 1) -> None:
        """
        Description:
            Invokes the detach() module of the UE component
        Parameters:
            id (str): The user equipment id to be detached from the network
            cell_id (int): The cell ID to detach the UE from the network, with default value of 1
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        logger.info(f"Detaching UE: {id}", also_console=True, banner=True)
        UE = self.testline.get_component_by_id(id)
        if UE:
            UE.detach(id, cell_id)
            if UE.state != State.Detached.value:
                raise Exception("CELL-{}:{} detach failed, exiting".format(cell_id, id))
        else:
            raise Exception("UE {} doesn't exist".format(id))

    def multiple_ues_detach_one_cell(self, cell_id: int, ue_ids: list) -> None:
        """
        Description:
            This function will dettach the provided UE from the corresponding cell_id in the network
        Parameters:
            cell_id (int): The cell ID will be detached to
            ue_ids (list): The list of start_ue and stop_ue want to detach. Note: ue_ids: [1,5] -> UE ID: 1,2,3,4,5
        Returns:
            None: This function only executes the codes and does not return any value.
        Example:
            Multiple UEs Detach One Cell    1    ${1,2}
        """
        logger.info("Detaching UEs from Cell", also_console=True, banner=True)
        start_ue_id = ue_ids[0]
        stop_ue_id = ue_ids[1]
        for ue_id in range(start_ue_id, stop_ue_id + 1):
            ue = self.testline.get_component_by_id(f"UE{ue_id}")
            logger.info(f"Detaching UE ID: {ue_id} from CELL ID: {cell_id}")
            ue.detach(f"UE{ue_id}", cell_id)
            if ue.state != State.Detached.value:
                raise Exception(
                    "CELL:UE {}:{} detach failed, exiting".format(cell_id, ue_id)
                )

    def multiple_ues_detach_multiple_cells(self, cells_and_ues: dict) -> None:
        """
        Description:
            This function will detach multiple UEs from the multiple Cells.
        Parameters:
            cells_and_ues (dict): The dictionary containt cell ID and UE ID
        Returns:
            None: This function only executes the codes and does not return any value.
        Example:
            Multiple UEs Detach Multiple Cells     { 1:@{1,3}, 2:@{4,6} }
            -> detach UE ID = 1,2,3 to CELL ID = 1
            -> detach UE ID = 4,5,6 to CELL ID = 2
        """
        logger.info("Detaching UEs from Cells", also_console=True, banner=True)
        for cell_id, ue_range in cells_and_ues.items():
            low, high = ue_range
            for ue_id in range(low, high + 1):
                ue_id = f"UE{ue_id}"
                logger.info(
                    f"Detaching UE ID: {ue_id} from CELL ID: {cell_id}",
                    also_console=True,
                )
                ue = self.testline.get_component_by_id(ue_id)
                ue.detach(ue_id, cell_id)
                if ue.state != State.Detached.value:
                    raise Exception(
                        "CELL:UE {}:{} detach failed, exiting".format(cell_id, ue_id)
                    )

    def start_traffic(
        self,
        id: str,
        traffic_type: str,
        interval: int,
        buffer_length: int,
        dl_iperf_port: str = None,
        ul_iperf_port: str = None,
        uplink_throughput: str = None,
        downlink_throughput: str = None,
        mss: str = None,
    ):
        """
        Description:
            This function will starts traffic over the network
        Parameters:
            id (str): The UE ID which to be sent traffic on
            traffic_type (str): Traffic type, TCP(Default)/UDP
            interval (int): Sets the interval time in seconds between periodic bandwidth, jitter, and loss reports
            buffer_length (int): The buffer length to read or write in bytes
            dl_iperf_port (str): The port number for DL Iperf
            ul_iperf_port (str): The port number for UL Iperf
            uplink_throughput (str): uplink traffic bandwidth to send
            downlink_throughput (str): downlink traffic bandwidth to send
            mss (str, optional): The maximum segment size for TCP traffic
        """
        traffic_started = False
        retries = 5
        UE = self.testline.get_component_by_id(id)
        core = self.testline.get_components_by_type("CORE")
        if isinstance(core, list) and len(core) > 0:
            core = core[0]

        for _ in range(retries):
            try:
                traffic_started = UE.start_traffic(
                    id,
                    core_object=core,
                    traffic_type=traffic_type,
                    interval=interval,
                    buffer_length=buffer_length,
                    dl_iperf_port=dl_iperf_port,
                    ul_iperf_port=ul_iperf_port,
                    uplink_throughput=uplink_throughput,
                    downlink_throughput=downlink_throughput,
                    mss=mss,
                    TL_name=self.TL_name,
                )
                break
            except IperfException:
                logger.info(
                    "Iperf UDP issue (MP-34879) hit, retrying traffic send",
                    also_console=True,
                )
                continue

        self.traffic_type = traffic_type
        if traffic_started:
            logger.info(
                "====== Sending traffic started successfully \n", also_console=True
            )
        else:
            raise Exception("Couldn't started traffic successfully\n")

    def send_traffic(
        self,
        id: str,
        traffic_type: str,
        duration: int,
        interval: int,
        buffer_length: int,
        dl_iperf_port: int = None,
        ul_iperf_port: int = None,
        uplink_throughput: str = None,
        downlink_throughput: str = None,
        mss: str = None,
    ) -> bool:
        """
        Description:
            This function will sends traffic over the network
        Parameters:
            id (str): The UE ID which to be sent traffic on
            traffic_type (str): Traffic type, TCP(Default)/UDP
            throughput (str): The Traffic bandwidth to send at
            duration (int): The time in seconds to transmit for
            interval (int): Sets the interval time in seconds between periodic bandwidth, jitter, and loss reports
            buffer_length (int): The buffer length to read or write in bytes
            dl_iperf_port (str): The port number for DL Iperf
            ul_iperf_port (str): The port number for UL Iperf
            uplink_throughput (str): uplink the Traffic bandwidth to send at
            downlink_throughput (str): downlink the Traffic bandwidth to send at
            mss (str, optional): The maximum segment size for TCP traffic
        Returns:
            traffic_sent (bool)
                True if traffic was send successfully
                False if traffic wasn't send successfully
        """
        logger.info("Sending Traffic", also_console=True, banner=True)
        traffic_sent = False
        retries = 5
        UE = self.testline.get_component_by_id(id)
        core = self.testline.get_components_by_type("CORE")
        if isinstance(core, list) and len(core) > 0:
            core = core[0]
        for _ in range(retries):
            try:
                traffic_sent = UE.send_traffic(
                    id=id,
                    core_object=core,
                    traffic_type=traffic_type,
                    duration=duration,
                    interval=interval,
                    buffer_length=buffer_length,
                    dl_iperf_port=dl_iperf_port,
                    ul_iperf_port=ul_iperf_port,
                    uplink_throughput=uplink_throughput,
                    downlink_throughput=downlink_throughput,
                    mss=mss,
                    TL_name=self.TL_name,
                )
                break
            except IperfException:
                logger.info(
                    "Iperf UDP issue (MP-34879) or (MP-51021) hit, retrying traffic send",
                    also_console=True,
                )
                continue

        self.traffic_type = traffic_type

        if not traffic_sent:
            raise Exception("====== Couldn't Send Traffic Successfully\n")

    def stop_traffic(self, id: str):
        """
        Description:
            This function will stops sending traffic over the network.
        Parameters:
            id (str): The UE ID which to be stopped traffic on
        Example:
            Stop Traffic
        """
        logger.info("Stopping Traffic", also_console=True, banner=True)
        UE = self.testline.get_component_by_id(id)
        core = self.testline.get_components_by_type("CORE")
        if isinstance(core, list) and len(core) > 0:
            core = core[0]

        traffic_stopped = UE.stop_traffic(id, core)
        if traffic_stopped:
            logger.info(
                "====== Sending traffic stopped successfully \n", also_console=True
            )

    def stop_traffic_all(self) -> None:
        """
        Description:
            This function will stops all traffic over the network.
        Parameters:
            None
        Returns:
            None
        Example:
            Stop Traffic All
        """
        logger.info("Stopping All Traffic", also_console=True, banner=True)
        UEs = self.testline.get_components_by_type("UE")
        core = self.testline.get_components_by_type("CORE")
        if isinstance(core, list) and len(core) > 0:
            core = core[0]
        for UE in UEs:
            traffic_stopped = UE.stop_traffic_all(core)
            if traffic_stopped:
                logger.info("====== Traffic stopped successfully \n", also_console=True)
            else:
                raise Exception("Couldn't stop traffic successfully\n")

    def send_traffic_multiple_ues(
        self,
        traffic_type: str,
        duration: int,
        interval: int,
        buffer_length: int,
        ue_ids: list,
        dl_iperf_port: str = None,
        ul_iperf_port: str = None,
        uplink_throughput: str = None,
        downlink_throughput: str = None,
        mss: str = None,
    ) -> None:
        """
        Description:
            Send traffic with multiple UEs in parallel.
            It will start the traffic, after duration, stop all traffic.
        Parameters:
            traffic_type (str): Traffic type, TCP(Default)/UDP
            duration (int): The time in seconds to transmit for
            interval (int): Sets the interval time in seconds between periodic bandwidth, jitter, and loss reports
            buffer_length (int): The buffer length to read or write in bytes
            ue_ids (list): The list of start_ue and stop_ue want to send traffic. Ex: ue_ids: [1,5] -> UE ID: 1,2,3,4,5
            dl_iperf_port (str): The DL IPerf Port number
            ul_iperf_port (str): The UL IPerf Port number
            uplink_throughput (str): uplink the Traffic bandwidth to send at
            downlink_throughput (str): downlink the Traffic bandwidth to send at
            mss (str): The maximum segment size for TCP traffic
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        logger.info("Sending Traffic for Multiple UEs", also_console=True, banner=True)
        traffic_started = self.start_traffic_multiple_ues(
            traffic_type,
            interval,
            buffer_length,
            ue_ids,
            dl_iperf_port,
            ul_iperf_port,
            duration,
            uplink_throughput,
            downlink_throughput,
            mss,
        )
        self.traffic_type = traffic_type
        core = self.testline.get_components_by_type("CORE")[0]

        if not traffic_started:
            raise Exception("Couldn't send traffic successfully\n")

        logger.info("Traffic sending in progress, please wait ...", also_console=True)
        time.sleep(int(duration) + 10)
        start_ue_id = ue_ids[0]
        stop_ue_id = ue_ids[1]
        for ue_id in range(start_ue_id, stop_ue_id + 1):
            ue_id = f"UE{ue_id}"
            ue = self.testline.get_component_by_id(ue_id)
            traffic_stopped = ue.stop_traffic(ue_id, core)
            if traffic_stopped:
                logger.info(
                    f"====== Duration of sending traffic is now complete. "
                    f"Traffic stopped successfully on UE {ue_id}",
                    also_console=True,
                )
            else:
                raise Exception("Couldn't stop traffic successfully\n")

    def start_traffic_multiple_ues(
        self,
        traffic_type: str,
        interval: int,
        buffer_length: int,
        ue_ids: list[int],
        dl_iperf_port: str = None,
        ul_iperf_port: str = None,
        duration: int = None,
        uplink_throughput: Optional[str] = None,
        downlink_throughput: Optional[str] = None,
        mss: Optional[str] = None,
    ) -> bool:
        """
        Description:
            Starts sending traffic with multiple UEs in parallel
        Parameters:
            traffic_type (str): Traffic type, TCP(Default)/UDP
            interval (int): Sets the interval time in seconds between periodic bandwidth, jitter, and loss reports
            buffer_length (int): The buffer length to read or write in bytes
            ue_ids (list): The list of start_ue want to send traffic. Ex: ue_ids: [1,5] -> UE ID: 1,2,3,4,5
            dl_iperf_port (str): The port number for DL Iperf
            ul_iperf_port (str): The port number for UL Iperf
            duration (int, optional): The time in seconds to transmit for
            uplink_throughput (str): uplink the Traffic bandwidth to send at
            downlink_throughput (str): downlink the Traffic bandwidth to send at
            mss (str, optional): The maximum segment size for TCP traffic
        Returns:
            traffic_started (bool): True if traffic sent successfully, raises exception otherwise
        """
        low, high = ue_ids
        core = self.testline.get_components_by_type("CORE")[0]

        # UL port should follow the formula: QFI = ((PORT_NUM - 6999) % (64)). (Port Range 6999 – 14000)
        # example: port number can be 7008, 7008+64=7072, 7072+64=7136
        for ue_id in range(low, high + 1):
            ue_id = f"UE{ue_id}"
            ue = self.testline.get_component_by_id(ue_id)

            logger.info(f"Send Traffic on UE ID: {ue_id}", also_console=True)

            cur_dl_iperf_port = (
                ue.dl_iperf_port
                if (not dl_iperf_port and downlink_throughput)
                else dl_iperf_port
            )
            cur_ul_iperf_port = (
                ue.ul_iperf_port
                if (not ul_iperf_port and uplink_throughput)
                else ul_iperf_port
            )

            only_uplink = uplink_throughput and not downlink_throughput
            both_ul_dl = uplink_throughput and downlink_throughput
            if (only_uplink or both_ul_dl) and int(cur_ul_iperf_port) > 14000:
                raise Exception(
                    f"ul_iperf_port is {cur_ul_iperf_port}, port should be smaller than 14000."
                )

            traffic_started = ue.start_traffic(
                ue_id,
                core,
                traffic_type,
                interval,
                buffer_length,
                cur_dl_iperf_port,
                cur_ul_iperf_port,
                uplink_throughput,
                downlink_throughput,
                mss,
                duration,
                self.TL_name,
            )
            self.traffic_type = traffic_type

            ul_iperf_port = (
                str(int(cur_ul_iperf_port) + 64) if cur_ul_iperf_port else None
            )
            if not traffic_started:
                logger.info(
                    f"====== Sending traffic on UE ID {ue_id} failed.",
                    also_console=True,
                )
                raise Exception("Couldn't send traffic successfully\n")

        return True

    def stop_traffic_multiple_ues(self, ue_ids: list) -> None:
        """
        Description:
            Stops sending traffic over the network
        Parameters:
            ue_ids (list): The list of start_ue want to send traffic. Ex: ue_ids: [1,5] -> UE ID: 1,2,3,4,5
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        low, high = ue_ids
        core = self.testline.get_components_by_type("CORE")[0]
        for ue_id in range(low, high + 1):
            logger.info(f"Stop Traffic on UE ID: {ue_id}", also_console=True)
            ue_id = f"UE{ue_id}"
            ue = self.testline.get_component_by_id(ue_id)
            ue.stop_traffic(ue_id, core)

    def send_traffic_pdu_session(
        self,
        traffic_type: str,
        direction: str,
        throughput: str,
        duration: int,
        interval: int,
        buffer_length: int,
        pdu_ips: str,
        ports: str,
        mss: Optional[str] = None,
        ue_id: Optional[str] = None,
    ) -> None:
        """
        Description:
            Sends traffic with specific pdu session. The format of iperf report is Mbits (iperf -f m).
        Parameters:
            traffic_type (str): The traffic type, TCP(Default)/UDP.
            direction (str): The traffic direction, uplink/downlink.
            throughput (str): The Traffic bandwidth to send. For iperf arg: -b
            duration (int): The time in seconds to transmit for. For iperf arg: -t
            interval (int): The interval time in seconds between periodic bandwidth report. For iperf arg: -i
            buffer_length (int): The buffer length to read or write in bytes. For iperf arg: -l
            pdu_ips (str): PDU Session IPs, can be one: ip1, or multiple PDU session IPs: [ip1, ip2, ...]
            ports (str): The port numbers for the traffic, can be 1 port: port1,  or multiple ports [port1, port2,...]
            mss (str, optional): The maximum segment size for TCP traffic
            ue_id (str, optional): The ID of the UE to send traffic
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        ip_pattern = r"(\d+\.\d+\.\d+\.\d+)"
        pdu_ip_list = re.findall(ip_pattern, pdu_ips)

        port_pattern = r"(\d+)"
        port_list = re.findall(port_pattern, ports)

        if ue_id is None:
            ue = self.testline.get_components_by_type("UE")[0]
        else:
            ue = self.testline.get_component_by_id(ue_id)

        logger.info(
            f"Send Traffic on PDU SESSION IP: {pdu_ip_list}, with PORT NUM: {port_list}",
            also_console=True,
        )

        # Use the named arguments to match UE method arguments as their order is different to that of calling method
        ret = ue.send_traffic_pdu_session(
            traffic_type=traffic_type,
            direction=direction,
            throughput=throughput,
            duration=duration,
            interval=interval,
            buffer_length=buffer_length,
            pdu_ip_list=pdu_ip_list,
            port_list=port_list,
            mss=mss,
            TL_name=self.TL_name,
        )
        self.traffic_type = traffic_type
        # Raise exception if failed to sent traffic
        if not ret:
            raise Exception("Traffic sent failed, exiting")

    def trigger_measurement_rpt_and_validate_handover(
        self,
        neighbor_cell: str,
        rsrp: str,
        rsrq: str,
        SERV_RSRP: int = None,
        SERV_RSRQ: int = None,
        eventType: int = None,
        ALL_PCI: int = None,
        id: str = None,
    ):
        """
        Description:
            Trigger measurement report from UEsim
        Parameters:
            NGH_PCI(str): is for neighbor_cell it's constant and set to 2,3,4,5,6
            rsrp(str):is for reference signal received power: (Neighbor cell rsrp) it's constant and set to 24,25,26,28,27
            rsrq(str) :is for Signal Received Quality it's constant and set to 25,26,27,29,28
            SERV_RSRP(int)/optional: is for Serving Cell Signal Received power  (Serving cell rsrp)
            SERV_RSRQ(int)/optional: is for Serving Cell Signal Received quality
            eventType(int)/optional:is for eventType()
            ALL_PCI(int)/optional:is for Physical Cell ID (range 0 to 1)
            id(str): The UE ID
        Raises:
            Exception: If handover process is failed.
        """
        logger.info("Triggering Measurement Report from UEsim", also_console=True, banner=True)
        # This keyword use for UE simulation
        if id is not None:
            ue = self.testline.get_component_by_id(id)
        else:
            logger.info(
                "====== No component id provided. So, The function trigger_measurement_rpt will be running on the first UE"
            )
            ue = self.testline.get_components_by_type("UE")[0]
            id = ue.id[0]
        trigger_status = ue.trigger_measurement_rpt(
            neighbor_cell, rsrp, rsrq, SERV_RSRP, SERV_RSRQ, eventType, ALL_PCI, id
        )
        if not trigger_status:
            raise Exception("Handover failed, exiting")

    def check_coredumps(self, component_ids: Optional[List] = []) -> None:
        """
        Description:
            This keyword provide method to check if Coredumps are found for particular component.
        Parameters:
            components_ids (list): To check coredumps for certain components, by default all components will be checked.
        """
        if component_ids:
            tl_components = [self.testline.get_component_by_id(component) for component in component_ids]
        else:
            tl_components = self.testline.components
        for component in tl_components:
            comp_status = component.status()
            if comp_status != OperationalStatus.CRASHED.value:
                continue
            else:
                raise FrameworkException("===== Coredumps found, please check logs for more info")
        logger.info("None of the components reported a coredump",
                    also_console=True
                    )

    def modify_config_file_xpath(self, *components_id: str, yaml_template: str) -> None:
        """
        Description:
            Modifies configuration files by using the xpath by xml file specified in a YAML file.
        Parameters:
            components_id: The component id want to update configuration.
            yaml_template (str): The YAML file contain the custom configuration.
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        logger.info(
            f"====== Modify config file using xpath: component_dict: {components_id}, yaml_template: {yaml_template}",
            also_console=True,
        )
        try:
            custom_yaml_dict = utils.read_yaml_file(
                yaml_template
            )

            for component_id in components_id:
                component_object = self.testline.get_component_by_id(component_id)
                if os.path.isdir(
                    f"{Keywords.test_case_directory_path}/{component_object.type}/{component_id}/{Global_Variables.Modified_Configs}/"
                ):
                    modify_config_folder = f"{Keywords.test_case_directory_path}/{component_object.type}/{component_id}/{Global_Variables.Modified_Configs}/"
                else:
                    modify_config_folder = os.path.join(os.getcwd(), f"{component_id}")
                    if not os.path.exists(modify_config_folder):
                        os.makedirs(modify_config_folder)

                config_file_path = component_object.config_file_path
                # Get golden config from test line to test runner.
                for config_type in custom_yaml_dict[
                    component_object.type.lower()
                ].keys():
                    if (
                        "config_file_name"
                        in custom_yaml_dict[component_object.type.lower()][config_type]
                    ):
                        config_file_name = custom_yaml_dict[
                            component_object.type.lower()
                        ][config_type]["config_file_name"]
                    elif hasattr(component_object, "config_file_name"):
                        config_file_name = component_object.config_file_name
                    else:
                        raise FrameworkException(
                            f"Could not found config_file_name for config_type: {config_type} in both yaml_template: {yaml_template} and inventory"
                        )
                    if (
                        "xml" not in config_type
                        and "Podman" in component_object.__class__.__name__
                    ):
                        container_config_path = component_object.container_cfg_path
                        # Get golden config file if not xml file.
                        utils.get_file_from_container(
                            component_object,
                            f"{container_config_path}/{config_file_name}",
                            f"{config_file_path}/{config_file_name}",
                        )
                    local_config_file = os.path.join(
                        modify_config_folder,
                        f"{component_id.lower()}_{config_file_name}",
                    )
                    lgtr.copy_file_scp(
                        component_object.connection,
                        f"{config_file_path}/{config_file_name}",
                        local_config_file,
                    )
                    # Modify config file by using xml xpath and delta configuration
                    (
                        ret,
                        modified_config_file_path,
                    ) = ConfigModification().generate_config_file_xpath(
                        Component(component_object.type.lower()),
                        yaml_template,
                        local_config_file,
                        config_type,
                    )
                    custom_yaml_dict[component_object.type.lower()][config_type].update(
                        {"target_cfg": os.path.basename(modified_config_file_path)}
                    )
                    if ret:
                        modified_cfg_file = custom_yaml_dict[
                            component_object.type.lower()
                        ][config_type]["target_cfg"]
                        logger.info(
                            f"\nComponent: {component_id}: Modified config files: {modified_cfg_file}\n",
                            also_console=True,
                        )
                    else:
                        raise FrameworkException(
                            f"\nComponent: {component_id}: Failed to modify config files.\n",
                            also_console=True,
                        )

                component_custom_dict = custom_yaml_dict[component_object.type.lower()]
                (
                    modified_cfg_path,
                    modified_cfg_file,
                ) = ConfigModification().copy_config_file(
                    component_object,
                    component_custom_dict,
                    modify_config_folder,
                    use_xpath=True,
                )
                if modified_cfg_file:
                    component_object.modified_config_file = modified_cfg_file

                if "Podman" in component_object.__class__.__name__:
                    component_extra_param = ""
                    for component_config in component_custom_dict.keys():
                        if (
                            ".xml"
                            not in component_custom_dict[component_config]["target_cfg"]
                        ):
                            component_extra_param = (
                                f"{component_extra_param} -v {modified_cfg_path}"
                                f"{component_custom_dict[component_config]['target_cfg']}"
                                f":{component_object.container_cfg_path}"
                                f"{component_custom_dict[component_config]['cfg_in_docker']}"
                                " "
                            )
                            logger.info(
                                f"\nComponent: {component_id} Add param {component_extra_param} to start podman {component_id.upper()}"
                            )
                        else:
                            # TODO for configuration files which can used by netconf-console
                            pass
                    component_object.extra_param = component_extra_param
                elif "BareMetal" in component_object.__class__.__name__:
                    for component_config in component_custom_dict.keys():
                        if (
                            ".xml"
                            not in component_custom_dict[component_config]["target_cfg"]
                        ):
                            original_config_file_name = component_custom_dict[
                                component_config
                            ]["origin_cfg"]
                            modified_config_file_name = component_custom_dict[
                                component_config
                            ]["target_cfg"]
                            self.txt_modified_components[
                                component_id.upper()
                            ] = original_config_file_name
                            component_object.connection.sendCommand_shell(
                                f"sudo cp {modified_cfg_path}/{modified_config_file_name} {modified_cfg_path}/{original_config_file_name}"
                            )
                        else:
                            # TODO for configuration files which can used by netconf-console
                            pass
                else:
                    # TODO for other component type
                    logger.warn(
                        f"Component: {component_id}: Do not support modify configuration with component {component_object.__class__.__name__}"
                    )
                logger.debug(
                    f"{component_id} - Modified netconf xml file components: {component_object.modified_config_file}, Extra parameters components: {component_object.extra_param}"
                )
        except Exception as e:
            raise FrameworkException(
                f"Fail to generate config file by xpath and delta! due to {str(e)}"
            )

    def get_performance_data(
        self,
        direction: str,
        reports_folder: str,
        feature_data_format: bool = False,
        id: str = None,
    ) -> None:
        """
        Description:
            Get specific data from csv log and txt command line log and push it into new csv log file
        Parameters:
            direction(str) : direction of traffic: "uplink" and "downlink" or "all"
            reports_folder(str) : Reports folder that contains a folder with csv log file
            feature_data_format (bool, optional): If you want to enable data collection for feature test. Defaults to False.
            id (str): The user equipment id wanted to get the performance data. The id of UE object. Ex: UE1.
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        if feature_data_format:
            destination_path = Keywords.test_suite_directory_path
        else:
            destination_path = Keywords.test_case_directory_path
        logger.info(
            f"Starting collect the specific data at {reports_folder}", also_console=True
        )
        if id is not None:
            UE = self.testline.get_component_by_id(id)
        else:
            UE = self.testline.get_components_by_type("UE")[0]
        UE.get_specific_data_performance(direction, reports_folder, destination_path)

    def start_podman_logs(self):
        """
        Description:
            start podman logs again to capture new logs starting from triggering this method
        Parameters:
            None
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        for component in self.testline.components:
            try:
                component.start_logs()
            except RuntimeError:
                pass

    # Call at test case setup
    def get_config_xml_from_components(self, components: list = None) -> None:
        # component_list : all
        # copy_file_scp from remote node to test_case's component specific config folder
        # lgtr.copy_file_scp(self.CUCP.connection, "component_xml_path","/data/MPFW_logs/Testsuite/testcasename/config")
        pass

    def validate_logs_structure_on_test_runner(
        self,
        pcap_capture_components: list = None,
        failed_component: str = None,
        copy_coredump: str = None,
        tar_files: bool = False,
    ) -> None:
        """
        Description:
            validate bin logs, console logs, and pcap files of all components on the test runner
        Parameters:
            copy_coredump (str):
            pcap_capture_components (list): list components want to capture pcap
            tar_files (bool, optional): If the transferred logs get tar files when copying to the test runner if true search for "full_log_{timestamp}.tar.gz"
            search for {component_logs}.tar.gz . Defaults to False.
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        if self.log_manager.log_mode.lower() == LogManager.NO_MODE:
            return None

        if copy_coredump is None:
            copy_coredump = BuiltIn().get_variable_value("${COREDUMP}")
        # update component list from started components list
        components_list = self.list_components_started.copy()
        if failed_component:
            if not Keywords.test_suite_directory_path:
                raise Exception("Test Suit directory on test runner does not exist")
            directory_path = Keywords.test_suite_directory_path
        else:
            if not Keywords.test_case_directory_path:
                raise Exception("Test Case directory on test runner does not exist")
            directory_path = Keywords.test_case_directory_path

        for component in self.list_components_started:
            if component.type == "L1":
                components_list.remove(component)

        logger.info("Starting log validation on the test runner..", also_console=True)
        for component in components_list:
            logger.info(
                f"Logs Validation is in progress for the component: "
                f"{component.id[0] if (component.type == 'UE' and type(component.id) is list) else component.id}",
                also_console=True,
            )
            if "Podman" not in type(component).__name__:
                if component.type in ["CUCP", "CUUP", "DU", "RU"]:
                    if (
                        pcap_capture_components
                        and component.id in pcap_capture_components
                    ):
                        CoreKeywords.__validate_logs_structure_on_test_runner(
                            component=component.type,
                            component_type="E2E",
                            transferred_core_component=False,
                            tar_files=tar_files,
                            component_directory=f"{directory_path}/"
                            f"{component.type.lower()}/"
                            f"{component.id.lower()}/",
                            transferred_pcap=True,
                            transferred_coredump=copy_coredump,
                        )

                    else:
                        CoreKeywords.__validate_logs_structure_on_test_runner(
                            component=component.type,
                            component_type="E2E",
                            transferred_core_component=False,
                            tar_files=tar_files,
                            component_directory=f"{directory_path}/"
                            f"{component.type.lower()}/"
                            f"{component.id.lower()}/",
                            transferred_pcap=False,
                            transferred_coredump=copy_coredump,
                        )

                    # to add Mplane in E2E Setup in logs validation
                    if (
                        component.type == "DU"
                        and hasattr(component, "mplane_start_script")
                        and component.mplane_start_script == "start_mplane"
                    ):
                        logger.info(
                            f"{component.id} - Logs Validation is in progress for the component: MPLANE",
                            also_console=True,
                        )
                        CoreKeywords.__validate_logs_structure_on_test_runner(
                            component="MPLANE",
                            component_type="E2E",
                            transferred_core_component=False,
                            tar_files=tar_files,
                            component_directory=f"{directory_path}/"
                            f"{component.type.lower()}/"
                            f"{component.id.lower()}/",
                            transferred_pcap=False,
                            transferred_coredump=copy_coredump,
                            skip_config=True,
                        )
                        logger.info(
                            f"{component.id} - Logs Validation is done for the component: MPLANE",
                            also_console=True,
                        )
                else:
                    logger.info(
                        f"Logs Validation skipped for the component: {component.id}",
                        also_console=True,
                    )
            else:
                if component.type == "UE" and type(component.id) is list:
                    if (
                        pcap_capture_components
                        and component.id[0] in pcap_capture_components
                    ):
                        CoreKeywords.__validate_logs_structure_on_test_runner(
                            component=component.type,
                            component_type="PAL",
                            transferred_core_component=True,
                            tar_files=tar_files,
                            component_directory=f"{directory_path}/"
                            f"{component.type.lower()}/"
                            f"{component.id[0].lower()}/",
                            transferred_pcap=True,
                            transferred_coredump=copy_coredump,
                        )
                    else:
                        CoreKeywords.__validate_logs_structure_on_test_runner(
                            component=component.type,
                            component_type="PAL",
                            transferred_core_component=True,
                            tar_files=tar_files,
                            component_directory=f"{directory_path}/"
                            f"{component.type.lower()}/"
                            f"{component.id[0].lower()}/",
                            transferred_pcap=False,
                            transferred_coredump=copy_coredump,
                        )
                elif component.type == "CORE":
                    for sub_core_name in ["XFE", "UPF", "SMF", "AMF"]:
                        if (
                            pcap_capture_components
                            and component.id in pcap_capture_components
                        ):
                            CoreKeywords.__validate_logs_structure_on_test_runner(
                                component=sub_core_name,
                                component_type="PAL",
                                transferred_core_component=True,
                                tar_files=tar_files,
                                component_directory=f"{directory_path}/"
                                f"{component.type.lower()}/"
                                f"{component.id.lower()}/"
                                f"{sub_core_name.lower()}/",
                                transferred_pcap=True,
                                transferred_coredump=copy_coredump,
                            )
                        else:
                            CoreKeywords.__validate_logs_structure_on_test_runner(
                                component=sub_core_name,
                                component_type="PAL",
                                transferred_core_component=True,
                                tar_files=tar_files,
                                component_directory=f"{directory_path}/"
                                f"{component.type.lower()}/"
                                f"{component.id.lower()}/"
                                f"{sub_core_name.lower()}/",
                                transferred_pcap=False,
                                transferred_coredump=copy_coredump,
                            )
                else:
                    if (
                        pcap_capture_components
                        and component.id in pcap_capture_components
                    ):
                        CoreKeywords.__validate_logs_structure_on_test_runner(
                            component=component.type,
                            component_type="PAL",
                            transferred_core_component=True,
                            tar_files=tar_files,
                            component_directory=f"{directory_path}/"
                            f"{component.type.lower()}/"
                            f"{component.id.lower()}/",
                            transferred_pcap=True,
                            transferred_coredump=copy_coredump,
                        )
                    else:
                        CoreKeywords.__validate_logs_structure_on_test_runner(
                            component=component.type,
                            component_type="PAL",
                            transferred_core_component=True,
                            tar_files=tar_files,
                            component_directory=f"{directory_path}/"
                            f"{component.type.lower()}/"
                            f"{component.id.lower()}/",
                            transferred_pcap=False,
                            transferred_coredump=copy_coredump,
                        )

                    # to add Mplane in E2E Setup in logs validation
                    if (
                        component.type == "DU"
                        and hasattr(component, "mplane_start_script")
                        and component.mplane_start_script == "start_mplane -ru"
                    ):
                        logger.info(
                            f"{component.id} - Logs Validation is in progress for the component: MPLANE",
                            also_console=True,
                        )
                        CoreKeywords.__validate_logs_structure_on_test_runner(
                            component="MPLANE",
                            component_type="PAL",
                            transferred_core_component=False,
                            tar_files=tar_files,
                            component_directory=f"{directory_path}/"
                            f"{component.type.lower()}/"
                            f"{component.id.lower()}/",
                            transferred_pcap=False,
                            transferred_coredump=copy_coredump,
                            skip_config=True,
                        )
                        logger.info(
                            f"{component.id} - Logs Validation is done for the component: MPLANE",
                            also_console=True,
                        )
            logger.info(
                f"Logs Validation is done for the component: "
                f"{component.id[0] if (component.type == 'UE' and type(component.id) is list) else component.id}",
                also_console=True,
            )

    def __validate_logs_structure_on_test_runner(
        component: str,
        component_directory: str,
        component_type: str,
        transferred_core_component: bool,
        tar_files: bool,
        transferred_pcap: bool = True,
        transferred_coredump: str = "True",
        skip_config=False,
    ) -> None:
        """
        Description:
            validate the transfered files structure
        Parameters:
            components (str): the component want to validate the transfered files structure.
            components_directory (str): the directory of the component under specific TestCase E.g.  /data/DFW_logs/TC.
            component_type (str): type of component to be like E2E or PAL
            transferred_core_component (bool): flag to check transferred core components.
            tar_files (bool): If the transferred logs get tar files when copying to the test runner if true search for "full_log_{timestamp}.tar.gz" else search for {component_logs}.tar.gz.
            transferred_pcap (bool): it will skip search directory pcap default will be True.
            transferred_coredump (str): default will be 'True'.
            skip_config (bool): this flag skip check config directory by default it is False.
        Returns:
            None: This function only executes the codes and does not return any value.
        *** we didn't check yet the coredump files in the logs***
        """
        if (
            component in ["CORE", "XFE", "UPF", "SMF", "AMF"]
            and not transferred_core_component
        ):
            logger.debug(
                f"The component {component} its type is E2E so there is no logs transferred"
            )
            return

        yaml_file_path = "./resources/validation/Transferred_Logs_Files_Schema.yaml"
        validations_dict = utils.read_yaml_file(yaml_file_path)
        files_schema = validations_dict["TC"]
        for path, directories, files in os.walk(component_directory):
            if files:
                directory_name = os.path.split(path)[1]
                # I think it will be redundant as if not transferred pcap it will not enter if condition of files
                # as it will be empty
                if directory_name == "Pcap" and not transferred_pcap:
                    continue

                if directory_name == "Config" and skip_config:
                    continue

                if directory_name in ["Config", "Pcap"]:
                    files_filters_list = files_schema[component.upper()][directory_name]
                else:
                    # check if tar files flag set true to check if full logs found in the transferred logs or not
                    if tar_files:
                        status_of_files = "tar_files"
                        files_filters_list = files_schema[component.upper()][
                            status_of_files
                        ][directory_name]
                    else:
                        status_of_files = "untar_files"
                        # add the type of setup to get related logs to this setup in logs directory in component in test case on the local machine
                        files_filters_list = files_schema[component.upper()][
                            status_of_files
                        ][directory_name][component_type]

                if files_filters_list:
                    found_full_log = False
                    for file_filter in files_filters_list:
                        # ignore coredump if trasferred core dump is false
                        if (
                            "core_dump" in file_filter
                            and transferred_coredump != "True"
                        ):
                            continue
                        r = re.compile(file_filter)
                        # filter the files inside the directory that match the input filter from schema yaml
                        filtered_files = list(filter(r.match, files))
                        get_numbers_of_full_logs_filter = "^full_log_.*"
                        # example from input filters full_log_\d{2}_\d{2}_\d{4}_\d{6}.* then count number of filters like that to check number of full logs matches number of filters
                        # as the full log has no validation on the files inside the tar file without extract those tar file to not spam the disk space with files
                        number_of_full_logs = len(
                            list(
                                filter(
                                    re.compile(get_numbers_of_full_logs_filter).match,
                                    files_filters_list,
                                )
                            )
                        )
                        if filtered_files:
                            # check if found full log from previous iteration to skip this one and check if this filter related to full log or not
                            if found_full_log and bool(
                                re.search(get_numbers_of_full_logs_filter, file_filter)
                            ):
                                continue
                            else:
                                for file in filtered_files:
                                    if os.path.getsize(os.path.join(path, file)) < 1:
                                        logger.warn(
                                            f"the file {os.path.join(path, file)} is empty"
                                        )
                                    else:
                                        logger.info(
                                            f"the size of file {os.path.join(path, file)} is "
                                            f"{CoreKeywords.__get_file_size_to_string(os.path.getsize(os.path.join(path, file)))} "
                                        )
                                # check if there is filter related to full log and if number of full logs filter greater than 0
                                if number_of_full_logs > 0 and bool(
                                    re.search(
                                        get_numbers_of_full_logs_filter, file_filter
                                    )
                                ):
                                    # check number of full logs filter match the number of full logs in the directory
                                    if number_of_full_logs == len(filtered_files):
                                        logger.info(
                                            f"the number of compressed full logs files identical with the number of filters equals '{number_of_full_logs}'"
                                        )
                                    else:
                                        logger.warn(
                                            f"the number of compressed full logs files '{len(filtered_files)}' different than the number of filters '{number_of_full_logs}' please check and update the Files Schema"
                                        )
                                    # set found full log flag to True to skip the other full log filter in the same directory
                                    found_full_log = True
                        else:
                            logger.warn(
                                f"the files of component {component} that match filter {file_filter} is not found under directory {path}"
                            )
                else:
                    # condition here for config folder as config file not has schema to check with it so validate on logs and pcap folders only
                    logger.warn(
                        f"the component {component} has files under directory {path} and didn't found files filter "
                        f"in Transferred_Logs_Files_Schema yaml please update it"
                    )

    def __get_file_size_to_string(file_size: int) -> str:
        """
        Description:
            get the file size in string format as E.g the file is 10 KB
        Parameters:
            file_size (int): file size in integer formate
        Returns:
            file_size_string that hold size in string format as E.g the file is 10 KB
        *** we use it to format the size of each file in transferred logs***
        """
        size_list = ["B", "KB", "MB", "GB"]
        size_string = ""
        for i in range(len(size_list)):
            if file_size < 1000:
                size_string = str(file_size) + " " + size_list[i]
                break
            else:
                file_size /= 1000
        return size_string

    def get_the_number_of_cores_in_component_server(self, component_id: str) -> int:
        """
        Description:
            This function will get the number of cores in the component's server
        Parameters:
            component_id (str): Id of component that needs to get the information from it's server (i.e. CUCP1, CUUP1, DU1)
        Returns:
            num_cores (int): Returns successfully the number of cores in component's server
        """
        try:
            component_object = self.testline.get_component_by_id(component_id)
            component_object.connection.send_command_and_extract_output("sudo su")
            # Send command to get the number of cores in component's server
            num_cores = component_object.connection.send_command_and_extract_output(
                "lscpu | awk '/^CPU\\(s\\)/ {print $2}'"
            )
            num_cores = int(num_cores[0].split()[0])
            logger.info(
                f"The number of cores in the {component_id} component's server is: {num_cores}\n",
                also_console=True,
            )
        except Exception as exc:
            logger.error(
                f"Exception: Cannot get the number of cores in the {component_id} component's server with error:"
                + str(exc)
                + " occurred."
            )
            raise exc
        return num_cores

    def start_get_data_performance_from_component_server(
        self, duration: int, interval: int, component_id_list: list = None
    ) -> None:
        """
        Description:
            This function will start getting data performance from component server and input these data into output csv file.
            Ex: The output csv files will have format: [component_id]_performance.csv.
        Parameters:
            duration (int): The time in seconds to get data performance.
            interval (int): The interval time in seconds to get data performance.
            component_id_list (list): The list of component id which you will start to get data performance.
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        logger.info("Starting Getting Performance Data from Component Server", also_console=True, banner=True)
        component_ids = []
        if component_id_list:
            component_ids = component_id_list
        else:
            for component in self.testline.components:
                if component.type in ["CUCP", "CUUP", "DU"]:
                    component_ids.append(component.id)

        for component_id in component_ids:
            logger.info(
                f"Starting to get data performance on component - id: {component_id}\n",
                also_console=True,
            )
            testline_component = self.testline.get_component_by_id(component_id)
            lgtr.start_get_data_performance_from_component_server(
                testline_component, duration, interval
            )

    def stop_get_data_performance_from_component_server(
        self, component_id_list: list = None
    ) -> None:
        """
        Description:
            This function will stop getting data performance on component server and input these data into output csv file.
            After getting data performance successfully, the output csv files will be transferred from component server to test suite folder in test runner.
        Parameters:
            component_id_list (list): The list of component servers which you will stop getting data performance.
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        logger.info("Stopping Getting Performance Data from Component Server", also_console=True, banner=True)
        component_ids = []
        if component_id_list:
            component_ids = component_id_list
        else:
            for component in self.testline.components:
                if component.type in ["CUCP", "CUUP", "DU"]:
                    component_ids.append(component.id)

        for component_id in component_ids:
            logger.info(
                f"Stopping to get data performance on component - id: {component_id}\n",
                also_console=True,
            )
            testline_component = self.testline.get_component_by_id(component_id.upper())
            lgtr.stop_get_data_performance_from_component_server(
                testline_component, Keywords.test_case_directory_path, self.log_manager
            )

    def clean_up_resources(self) -> None:
        """
        Description:
            Clean up the resources at the end of test case.
        Parameters:
            None.
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        logger.info("Cleaning Up Resources", also_console=True, banner=True)
        clean_up_resources_succ = {}
        components = self.testline.components
        for component in components:
            try:
                if type(component.id) is list:
                    modified_components = any(
                        id.upper() in self.txt_modified_components.keys()
                        for id in component.id
                    )
                else:
                    modified_components = (
                        component.id.upper() in self.txt_modified_components.keys()
                    )
                component.clean_up_resources(modified_components)
                component.modified_config_file = None
                component.extra_param = None
            except Exception as e:
                if type(component.id) is list:
                    clean_up_resources_succ[component.type if isinstance(component.id, list) else component.id] = e
                else:
                    clean_up_resources_succ[component.id] = e
        if len(clean_up_resources_succ.keys()):
            raise FrameworkException(str(clean_up_resources_succ))

    def reboot_server_ssh(self, component_id: str) -> None:
        """
        Description:
            The purpose of the method is to reboot a given component's server via the SSH terminal.
        Parameters:
            component_id (str): Id of component that needs to be rebooted (i.e. CUCP1, CUUP1, DU1)
        Returns:
            None. The method prints the state whether the server is back to ON or not (so, there will be no return value).
        """

        component_object = self.testline.get_component_by_id(component_id)
        if hasattr(component_object, "connection"):
            if component_object.connection.windows_platform:
                raise FrameworkException(
                    f"The component {component_id} do not support for ssh rebooting. Please check!"
                )
        else:
            raise FrameworkException(
                f"The component {component_id} do not support for ssh rebooting. Please check!"
            )
        server_ip = component_object.ip

        logger.info(
            "\n======Rebooting the server "
            + server_ip
            + " (component:"
            + component_object.type
            + ")",
            also_console=True,
        )
        component_object.connection.sendCommand_shell("sudo su")
        component_object.connection.sendCommand_shell("sudo reboot")
        host_up = False
        timer = 0
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Waiting for a maximum of 5 minutes for the server to be ready for SSH after reboot
        logger.info(
            "- INFO, Waiting till the server is ready for SSH after reboot",
            also_console=True,
        )
        while timer <= 4:
            time.sleep(60)
            timer += 1
            try:
                s.connect((server_ip, 22))
                host_up = True
                break
            except socket.error:
                logger.info("Server still rebooting...", also_console=True)
        s.close()
        if host_up:
            logger.info(
                "\n======The server is back online and is ready for SSH!\n",
                also_console=True,
            )
            for comp in self.testline.components:
                if comp.ip == server_ip:
                    comp.connection = SSHConnection(
                        component_object.ip,
                        component_object.username,
                        component_object.password,
                        Global_Variables.ssh_port,
                    )
        else:
            raise Exception(
                "======The server is not ready for SSH despite the power state being ON in iDRAC"
                " even after 5 minutes!"
            )

    def stop_components(self, *components: list) -> None:
        """
        Description:
            The purpose of the method is to stop the specific components of the test line.
        Parameters:
            components (list): components list  which need to be stopped (i.e. AMF, SMF, UPF, CUCP, CUUP, EU)
        Returns:
            None. The method prints the state whether the components are stopped or not (so, there will be no return value).
        """
        # stop the components

        for item in components:
            component = item.upper()
            if (
                component == "AMF"
                or component == "SMF"
                or component == "UPF"
                or component == "XFE"
            ):
                self.component_obj_dict["CORE"].stop_core_components(component)
            else:
                self.component_obj_dict[component].stop()

    def get_ue_ip(self, id: str = None, pdu_session_num: int = None) -> str:
        """
        Description:
            The purpose of method is to get ip address of ue after ue has attached.
        Parameters:
            id (str): The id of UE object. Ex: UE1.
            pdu_session_num(int): the associated pdu session id.
        Returns:
            ue_ip(str): the assigned ip address after ue attached . Otherwise, raise exception.
        """
        ue_ip = None
        if id is not None:
            UE = self.testline.get_component_by_id(id)
        else:
            UE = self.testline.get_components_by_type("UE")[0]
            if type(UE.id) is list:
                id = UE.id[0]
            else:
                id = UE.id
        if "Podman" in UE.__class__.__name__:
            ue_ip = UE.get_ue_ip(id, pdu_session_num)
        else:
            ue_ip = UE.get_ue_ip(id)
        if ue_ip == "0.0.0.0":
            raise Exception(f"Failed to get IP of UE {id}, existing\n")
        return ue_ip

    def ue_attach_fail_type(
        self,
        cell_id: str,
        scenario: str,
        fail_type: str,
        delay: int = 10,
        drop_count: int = 1,
        id: str = None,
    ) -> None:
        """
        Description:
            The purpose of method is to attach ue with fail scenario.
        Parameters:
            cell_id (int): the cell id.
            scenario (str): includes 'setup_fail','request_fail','reconfig_fail','registration_fail','sec_mode_comp_fail'.
            failure_type (str): type of failure 'drop' or 'delay'
            id (str): The id of UE object. Ex: UE1.
        Returns:
            None. The method prints the state whether the failed attach case can be triggered with or not (so, there will be no return value).
        """
        if id is not None:
            UE = self.testline.get_component_by_id(id)
        else:
            UE = self.testline.get_components_by_type("UE")[0]
            if type(UE.id) is list:
                id = UE.id[0]
            else:
                id = UE.id
        UE.attach_fail_type(cell_id, id, scenario, fail_type, delay, drop_count)

    def get_scell_mac_ce(self, id: str = None) -> str:
        """
        Description:
            Get SCELL INFO for a specific UE ID
        Parameters:
            id (str): The id of UE object. Ex: UE1.
        Returns:
            scell_info (str): SCELL info as string.
        """
        if id is not None:
            UE = self.testline.get_component_by_id(id)
        else:
            UE = self.testline.get_components_by_type("UE")[0]
            if type(UE.id) is list:
                id = UE.id[0]
            else:
                id = UE.id
        scell_info = UE.get_scell_mac_ce(id)
        if scell_info == "FAIL":
            raise Exception("Failed to get SCELL INFO of UE: {}\n".format(id))
        return scell_info

    def prepare_ue_capability_file(self, file_path: str, id: str = None) -> None:
        """
        Description:
            Transfer the ue capability file from test runner to test line then copy into running UESIM container.
            This keyword must be executed before using any attach-related keywords with flag 'with_ue_capability' set to True.
            Base on TL we have 3 implementations of UE.prepare_ue_capability_file
            Ex:
            Prepare UE Capability File    file_path=./resources/templates/ue/sa_ue_cap_config_mu1_n78_1CC.json
            UE Attach    1    with_ue_capability=True   id=UE1
        Parameters:
            file_path(str): path to the location where the ue capability file is stored.
            id (str): The id of UE object. Ex: UE1.
        Returns:
            same returns with UE.prepare_ue_capability_file
        """
        if id is not None:
            UE = self.testline.get_component_by_id(id)
        else:
            UE = self.testline.get_components_by_type("UE")[0]
        UE.prepare_ue_capability_file(file_path)

    def detach_all_ue(self) -> None:
        """
        Description:
            To send the detach all UEs command
            This command is put into test teardown to make sure all UEs will be clear if the current test failed before step detaching UEs
            Base on TL we have 2 implementations of UE.prepare_ue_capability_file
        Parameters:
            self (CoreKeywords) : a corekeywords object.
        Returns:
            same returns with UE.detach_all_ue.
        """
        logger.info("Detaching All UEs", also_console=True, banner=True)
        UEs = self.testline.get_components_by_classname("PodmanUESIM")
        if UEs:
            UEs[0].detach_all_ue()

    def send_command_shell(self, component_id: str, command: str) -> str:
        """
        Description:
            send_command_shell sends command to component server through SSH shell channel. It can support sending multiple
            dependent commands one by one, or sudo command with/without password required.
        Parameters:
            component_id (str): Id of component , eg: CUCP1 , CUUP1
            command (str): command sent to remote server
        Returns:
            output (str): output of the command
        """
        component = self.testline.get_component_by_id(component_id)
        ssh_connection = component.connection
        output = ssh_connection.sendCommand_shell(command)
        return output

    def send_command(self, component_id: str, command: str, ignore_err_message: str = "") -> str:
        """
        Description:
            send_command sends command to component server through SSH exec channel. It can support sending multiple
            independent commands one by one, or sudo command without password requried.
        Parameters:
            component_id (str): Id of component, eg: CUCP1, CUUP1
            command (str): command sent to remote server
            ignore_err_message (str): The specific error message you want to ignore.
        Returns:
            output (str): output of the command
        """
        component = self.testline.get_component_by_id(component_id)
        ssh_connection = component.connection
        output = ssh_connection.sendCommand(
            command, ignore_err_message=ignore_err_message
        )
        return output

    def speed_test(
        self,
        cuup_stats_ue_id: str = "65537",
        cuup_stats_tunnel_id: str = "1",
        server_url: str = "http://6.6.6.200:3000/?run",
        duration: int = 45,
        id: str = None,
        cuup_id: str = None,
        du_id: str = None,
    ) -> tuple[float, float, float, float]:
        """
        Description:
            This method use for trigger a speed test from the web browser in UE.
        Parameters:
            cuup_stats_ue_id (str): UE ID got from the CUUP stat log.
            cuup_stats_tunnel_id (str): the tunnal id in CUUP stat log.
            server_url (str): the url of the testing server
            duration(int)
            id(str):ID
            cuup_id(str): CUUP ID
            du_id(str): DU ID
        Return:
            return_speed["DU"]["DL"] (float): Speed of DL from DU (Mbps),
            return_speed["DU"]["UL"] (float): Speed of UL from DU (Mbps),
            return_speed["CUUP"]["DL"] (float): Speed of DL from CUUP (Mbps), also_console=True
            return_speed["CUUP"]["UL"] (float)" Speed of UL from CUUP (Mbps)
        """
        return_speed = {"CUUP": {}, "DU": {}}
        speed_stat_log = {"CUUP": {}, "DU": {}}
        try:
            if id is not None:
                UE = self.testline.get_component_by_id(id)
            else:
                UE = self.testline.get_components_by_type("UE")[0]
            UE.trigger_speed_test(server_url=server_url, duration=duration, ue_id=id)

            # Get the network speed from CUUP and DU with the first UE attach
            if cuup_id is not None:
                CUUP = self.testline.get_component_by_id(cuup_id)
            else:
                CUUP = self.testline.get_components_by_type("CUUP")[0]
            if du_id is not None:
                DU = self.testline.get_component_by_id(du_id)
            else:
                DU = self.testline.get_components_by_type("DU")[0]
            (
                speed_stat_log["CUUP"]["DL"],
                speed_stat_log["CUUP"]["UL"],
            ) = CUUP.get_throughput_from_stats_txt_file(
                cuup_stats_ue_id, cuup_stats_tunnel_id
            )[
                0::3
            ]
            speed_stat_log["DU"]["DL"] = self.log_manager.parse_stats_file(
                DU, "Cell Tpt Statistics", "CELL-ID", "1", "SCH-DL"
            )["SCH-DL"]
            speed_stat_log["DU"]["UL"] = self.log_manager.parse_stats_file(
                DU, "Cell Tpt Statistics", "CELL-ID", "1", "SCH-UL"
            )["SCH-UL"]

            # Filter value "" and get max value in the result
            for component in speed_stat_log:
                for direction in speed_stat_log[component]:
                    if speed_stat_log[component][direction] != []:
                        filter_list = list(
                            filter(
                                lambda a: a != "", speed_stat_log[component][direction]
                            )
                        )
                        throughput_max = max(list(map(float, filter_list)))
                        logger.info(
                            f"Result {component} ThroughPut {direction}: {throughput_max} Mbps",
                            also_console=True,
                        )
                        return_speed[component][direction] = throughput_max
                    else:
                        raise Exception(
                            f"Cannot get Throughput value of component: {component}!!!"
                        )
        except Exception as e:
            logger.error(
                "Exception: Cannot trigger speed test with error:"
                + str(e)
                + " occurred."
            )
        return (
            return_speed["DU"]["DL"],
            return_speed["DU"]["UL"],
            return_speed["CUUP"]["DL"],
            return_speed["CUUP"]["UL"],
        )

    def netconf_alarm_check(self, component_id: str, alarm_name: str, element_to_check: str, timeout: int = 60, interval_time: int = 5) -> list:
        """
        Description:
            netconf_alarm_check gets the alarmlist of the component through netconf-console command, search the alarm name and the sibling elements in the netconf-console command output.
        Parameters:
            component (str): component name, eg: CUCP, CUUP, DU...
            alarm_name (str): alarm_name to search
            element_to_check : element to search, search from the sibling elements of the alarm element with alarm_name. Ex. : alarmId, alarmType, alarmRaisedTime, perceivedSeverity. etc.
            timeout (int): Timeout value for the search alarm_name, in seconds.
            interval_time (int): Interval between consecutive checks, in seconds.
        Returns:
            element_text_list (array): text of the element_to_check
        """
        component = self.testline.get_component_by_id(component_id)
        netconf_alarmlist_cmd = (
            f"{Global_Variables.netconf_console_path}netconf-console "
            f"--host={component.oam_ip} "
            f"--port={Global_Variables.oam_port} "
            f"--user=netconf --privKeyType=rsa --privKeyFile={Global_Variables.NETCONF_PRIVATE_KEYPATH} "
            f"--get -x /ManagedElement/AlarmList"
        )
        time_out = time.time() + timeout
        while time.time() < time_out:
            netconf_alarm_output = self.send_command(
                component.id,
                netconf_alarmlist_cmd,
                ignore_err_message="CryptographyDeprecationWarning",
            )
            element_text_list = []
            # start processing the netconf command output
            tree = etree.fromstring(netconf_alarm_output.encode("utf-8"))
            # search the element with text=alarm_name
            alarm_list = tree.xpath(".//*[text()='" + alarm_name + "']/..")
            # if the element with text=alarm_name found, search the sibling elements with tag name=element_to_check
            if len(alarm_list):
                logger.info(f"alarm: {alarm_name} is found", also_console=True)
                for i in range(len(alarm_list)):
                    element_list = (
                        alarm_list[i]
                        .getparent()
                        .xpath(".//*[name()='" + element_to_check + "']")
                    )
                    # if the sibling elements with specific tag: element_to_check found, extract its text
                    if len(element_list):
                        for j in range(len(element_list)):
                            element_text = element_list[j].text
                            logger.info(
                                f"{element_to_check}: {element_text}", also_console=True
                            )
                            element_text_list.append(element_text)
                    else:
                        logger.info(
                            f"element tag: {element_to_check} is not found",
                            also_console=True,
                        )
                if element_text_list:
                    break

            time.sleep(interval_time)
        else:
            logger.info(f"alarm: {alarm_name} is NOT found", also_console=True)

        return element_text_list

    def replaceLineInFile(self, line_start: str, new_line: str, filepath: str, app_instance_id: str) -> bool:
        """
        Description:
        This function replaces a line in a text file

        Parameters:
        line_start (str): To identify the line that you want to edit/replace, you give it the text that exists in the file before the change.
        new_line (str): The new line that will replace the existing one.
        filepath (str): The path to the file.
        app_instance_id (str): The id of component on which the file exists.
        Returns:modify_config_file
        (Boolean): True, if the file was edited successfully, False, if an error occurred, or if an excetion occurred.
        """
        try:
            component = self.testline.get_component_by_id(app_instance_id)
            ssh_connection = component.connection
            ssh_connection.send_command_and_extract_output("sudo su")
            # Logging for debugging
            logger.info(
                f"\n====== replaceLineInFile on component [{app_instance_id}]",
                also_console=True,
            )
            logger.info("______________________", also_console=True)
            cmd_output = ssh_connection.send_command_and_extract_output(
                'sed -i "s/^' + line_start + ".*/" + new_line + '/" ' + filepath
            )

            # If the list is empty, means that the command was successful
            if not cmd_output:
                return True
            else:
                logger.info(cmd_output, also_console=True)
                return False
        except Exception as e:
            logger.error(
                "In [replaceLineInFile] function: Exception: "
                + str(e.__class__)
                + " occurred."
            )
            return False

    def getFileSize(self, filepath: str, component_id: str) -> int:
        """
        Description:
            This function returns the size of a given file.
        Parameters:
            filepath (str): The path to the file.
            component_id (str): The id of server component on which the file exists.
        Returns:
            size (int): File size, -1 if the file does NOT exist.
        """
        try:
            logger.info(
                f"\n===> [getFileSize] on component {component_id}", also_console=True
            )
            ssh_connection = self.testline.get_component_by_id(component_id).connection
            ssh_connection.sendCommand_shell("sudo su")
            ssh_connection.sendCommand_shell("sudo chmod -R 755 " + filepath)

            cmd_output_1 = ssh_connection.sendCommand_shell("stat " + filepath)
            if "No such file or directory" in cmd_output_1:
                return -1
            # string manipulation # step_1
            size = cmd_output_1.split("Blocks", 1)
            # string manipulation # step_2
            size = size[0].split("Size: ", 1)
            # here we got the cropped size number as int
            size = int(size[1])

            return size
        except Exception as e:
            logger.error(
                "In [getFileSize] function: Exception: "
                + str(e.__class__)
                + " occurred."
            )
            return -1

    def getTheNumberOfFilesInDirectory(self, path: str, pattern: str, component_id: str) -> int:
        """
        Description:
        This function returns the number of files in the given path.
        Parameters:
        filepath (str): The path to the directory.
        pattern (str): The file pattern you are searching for.
        component_id (str): The id of server on which the directory exists.
        Returns:
        numberOfFiles (int): The number of files in the given path. "-1" for any exceptions.
        (Boolean): False, If an error/exception has occurred.
        """
        try:
            logger.info(
                f"\n===> [getTheNumberOfFilesInDirectory] on componnent {component_id}",
                also_console=True,
            )
            ssh_connection = self.testline.get_component_by_id(component_id).connection
            ssh_connection.sendCommand_shell("sudo su")

            if pattern == "*":
                numberOfFiles = ssh_connection.send_command_and_extract_output(
                    "sudo ls " + path + " | wc -l"
                )
            else:
                numberOfFiles = ssh_connection.send_command_and_extract_output(
                    "find "
                    + path
                    + " -maxdepth 1 -type f -name '"
                    + pattern
                    + "' | wc -l"
                )

            # This means that an error has occurred, for example if the given path does not exist.
            if len(numberOfFiles) > 1:
                logger.info(numberOfFiles[0], also_console=True)
                return False

            numberOfFiles = numberOfFiles[0]

            return int(numberOfFiles)
        except Exception as e:
            logger.error(
                "In [getTheNumberOfFilesInDirectory] function: Exception: "
                + str(e.__class__)
                + " occurred."
            )
            return -1

    def compare_debug_cli_to_template(
        self, cli_cmd: str, template_file: str, cucp_id: str = None
    ) -> None:
        """
        Description:
            Invokes the compare_debug_cli_to_template() module in the CUCP component
        Parameters:
            cli_cmd (str): debug cli command.
            template_file (str): Corresponding template json file.
            cucp_id (str): The ID of CUCP component want to compare dubug cli to template.
                           If none is set will do for all CUCP component on Test Line. Default is None
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        logger.info("Comparing CUCP CLI to Template", also_console=True, banner=True)
        logger.info(
            "====== Comparing debug cli command output to Template\n", also_console=True
        )
        try:
            if cucp_id is None:
                testline_components = self.testline.get_components_by_type("CUCP")
                for testline_component in testline_components:
                    if (
                        testline_component.compare_debug_cli_to_template(
                            cli_cmd, template_file
                        )
                        is False
                    ):
                        raise FrameworkException(
                            f"Comparison failed for {testline_component.id}. "
                            f"Output of debug cli commands does not match with the corresponding template {template_file}"
                        )
            else:
                testline_component = self.testline.get_component_by_id(cucp_id)
                if (
                    testline_component.compare_debug_cli_to_template(
                        cli_cmd, template_file
                    )
                    is False
                ):
                    raise FrameworkException(
                        f"Comparison failed for {cucp_id}. "
                        f"Output of debug cli commands does not match with the corresponding template {template_file}"
                    )
            logger.info(
                f"====== Comparison successfully. "
                f"Output of debug cli commands matches with the corresponding template {template_file}\n",
                also_console=True,
            )
        except Exception as exc:
            raise FrameworkException(f"Comparison error: {str(exc)}")

    def trigger_pdu_modification_request_smf(
        self,
        id: str = None,
        pdu_session_modification_msg_id: int = 18,
        flow_mod_cond: int = 3,
        supi: int = 311480123456789,
        cli_pdu_sess_id: int = 5,
        five_qi: int = 9,
        ul_sess_ambr: int = 2000000000,
        dl_sess_ambr: int = 2000000000,
        ul_mbr: int = 1022000,
        dl_mbr: int = 1023000,
        ul_gbr: int = 1022000,
        dl_gbr: int = 1023000,
        flow_val_1: int = 9,
    ) -> None:
        """
        Description:
            Triggers the pdu modification request to SMF and verifies the response from smf.log
        Parameters:
            id(str): The Core ID
            :param pdu_session_modification_msg_id = 18 (default)
            :param flow_mod_cond = 3(default) for release
            :param supi = 311480123456789 (default) should match with the UESIM configuration
            :param cli_pdu_sess_id = 5 (default)
            :param five_qi = 9 (default)
            :param ul_sess_ambr = 2000000000 (default)
            :param dl_sess_ambr = 2000000000 (default)
            :param ul_mbr = 1022000 (default)
            :param dl_mbr = 1023000 (default)
            :param ul_gbr = 1022000 (default)
            :param dl_gbr = 1023000 (default)
            :param flow_val_1 = 9 (default)
        Returns:
            None
        """
        logger.info("Starting pdu modification request", also_console=True)
        try:
            if id is not None:
                core = self.testline.get_component_by_id(id)
            else:
                logger.info(
                    "====== No component id provided. So,The function trigger_pdu_modification_request_smf will be running on the first CORE"
                )
                core = self.testline.get_components_by_type("CORE")[0]
            rsys_cli_python_file = Path(r"./resources/smf/rsys_cli_py_2.py")
            test_runner_smf_log_directory = "./"
            if core.component_name_smf == "BareMetalSMF":
                smf_log_file = self.container_bin_path_smf + "smf.log"
            elif core.component_name_smf == "PodmanSMF":
                smf_log_file = f"{Global_Variables.e2e_path}/logs/smf/smf.log"
            else:
                raise Exception(
                    f"PDU modification command to SMF is not supported on the {core.component_name_smf} setup yet !"
                )
            if rsys_cli_python_file.is_file():
                scp_status_1 = lgtr.copy_file_scp(
                    core.connection, rsys_cli_python_file, Global_Variables.log_dir, method="put"
                )
                logger.info(f"scp rsys_cli_py2.py to SMF server : {scp_status_1}")
                if scp_status_1:
                    logger.info("Executing the rsys_cli script in SMF server")
                    core.connection.sendCommand_shell("sudo su")
                    core.connection.sendCommand_shell(
                        f"chmod a+rwx {Global_Variables.log_dir}/rsys_cli_py_2.py"
                    )
                    # A working set of arguments for the script to be run on core machine
                    #     "python2 /home/mrorange/rsys_cli_py_2.py 18 3 311480123456789 "
                    #     "5 9 2000000000 2000000000 1022000 1023000 1022000 1023000 9")
                    core.connection.sendCommand_shell(
                        f"python {Global_Variables.log_dir}/rsys_cli_py_2.py "
                        f"{pdu_session_modification_msg_id} {flow_mod_cond} "
                        f"{supi} {cli_pdu_sess_id} {five_qi} {ul_sess_ambr} "
                        f"{dl_sess_ambr} {ul_mbr} {dl_mbr} {ul_gbr} {dl_gbr} "
                        f"{flow_val_1} {core.smf_cli_ip} {core.smf_cli_port}"
                    )
                    logger.info(
                        "removing the script after execution on the core server"
                    )
                    core.connection.sendCommand_shell(
                        f"rm -f {Global_Variables.log_dir}/rsys_cli_py_2.py"
                    )

                    logger.info(
                        "Remove smf.log in the current directory if it is present"
                    )
                    smf_log_old = Path(f"{test_runner_smf_log_directory}/smf.log")
                    # set missing_ok to True so that it won't raise an exception in the absence of smf.log
                    smf_log_old.unlink(missing_ok=True)
                    logger.info("scp smf.log to the test runner")
                    scp_status_2 = lgtr.copy_file_scp(
                        core.connection, smf_log_file, test_runner_smf_log_directory
                    )
                    logger.info(f"scp smf.log to test runner : {scp_status_2}")
                    if scp_status_2:
                        logger.info(
                            "Checking the pdu session modification complete message in smf.log",
                            also_console=True,
                        )
                        with open("smf.log") as smf_file:
                            smf_log_lines = smf_file.readlines()
                            is_msg_found = False
                            for line in smf_log_lines:
                                if (
                                    line.upper().find(
                                        "RECEIVED PDU SESSION MODIFICATION COMPLETE UE >> SMF"
                                    )
                                    != -1
                                ):
                                    logger.info(
                                        f"line number: {smf_log_lines.index(line)}/{len(smf_log_lines)} ->"
                                        f" {line}",
                                        also_console=True,
                                    )
                                    is_msg_found = True
                            if not is_msg_found:
                                raise Exception(
                                    "Not found the message PDU Session Modification Complete UE >> SMF"
                                )
                    else:
                        raise Exception(
                            "smf.log cannot be transferred to the test runner"
                        )
                else:
                    raise Exception(
                        "rsys_cli_py_2.py script cannot be transferred to the SMF server"
                    )
            else:
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT))
        except Exception as exc:
            logger.error(f"PDU modification error: {str(exc)}")

    def du_debug_cli(self, cli_cmd: str, id: str = None) -> None:
        """
        Description:
            The method sends the debug CLI command with set or show parameter to DU component, and check whether there's
            'No error' in the show cmd output or 'Set Successful' in the set cmd output.
        Parameters:
            cli_cmd (str): debug cli command, set or show.
            id:            The id of DU object (Eg. DU1). Otherwise, send the debug CLI command to the first DU in yaml
        Returns:
            None. The method prints the output of the debug cli, raise exception if no 'No error' or 'Set Successful'
            found in the output.
        """
        logger.info("Checking DU CLI", also_console=True, banner=True)
        if id is not None:
            du_object = self.testline.get_component_by_id(id)
        else:
            du_object = self.testline.get_components_by_type("DU")[0]
        logger.info(
            f"====== Starting debug CLI on DU '{du_object.id}'", also_console=True
        )
        ret = du_object.du_debug_cli(cli_cmd)
        if not ret:
            raise FrameworkException(
                f"DU Debug CLI cmd on DU '{du_object.id}' is not successful, cmd is {cli_cmd}"
            )

    def compare_du_debug_cli(self, cli_cmd: str, template_file: str, id: str = None) -> bool:
        """
        Description:
            Invokes the compare_du_debug_cli() module in the DU component
        Parameters:
            cli_cmd (str):       debug cli command.
            template_file (str): Corresponding template json file.
            id:                  The id of DU object (Eg. DU1). Otherwise, the first DU in yaml file will be used
        Returns:
            (Bool) : True if Output of DU debug cli commands matches with the corresponding template;
            False if Output of DU debug cli commands does not match with the corresponding template
        """
        if id is not None:
            du_object = self.testline.get_component_by_id(id)
        else:
            du_object = self.testline.get_components_by_type("DU")[0]
        logger.info(
            f"====== Starting compare debug CLI on DU '{du_object.id}'",
            also_console=True,
        )
        ret = du_object.compare_du_debug_cli(cli_cmd, template_file)
        return ret

    def kill_ru_sim_instance(
        self,
        ru_sim_instance_ids: list[str] = None,
        ru_sim_port_ids: list[str] = None,
        component_id: str = None,
    ) -> None:
        """
        Description:
            This function will kill RU Sim instance id with RU Sim port correspondingly and verify it.
            NOTE: The index position in list ru_sim_instance_ids will correspond to the index position in list ru_sim_port_ids.
            Ex: ru_sim_instance_ids=["ru_sim_1", "ru_sim_2", "ru_sim_3", "ru_sim_4", "ru_sim_5"]
                ru_sim_port_ids=["7022", "3022", "4022", "5022", "6022"]
                Port 7022 corresponds to ru_sim_1, port 3022 corresponds to ru_sim_2,  port 4022 corresponds to ru_sim_3,..

        Parameters:
            ru_sim_instance_ids(list): The list of RU Sim instance ids. Ex: ru_sim_instance_ids=["ru_sim_1", "ru_sim_2", "ru_sim_3", "ru_sim_4", "ru_sim_5"]
                                       If ru_sim_instance_id is None, then default will get ru_sim_instance_id=["ru_sim_1"] in yaml file.
            ru_sim_port_ids(list): The list of RU Sim port number ids. Ex: ru_sim_port_ids=["7022", "3022", "4022", "5022", "6022"]
                                   If ru_sim_port_id is None, then default will get ru_sim_port=["7022"] in yaml file.
            component_id(str): component id. If id is None, then default will start first DU component.
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        if component_id is not None:
            du_object = self.testline.get_component_by_id(component_id)
        else:
            du_object = self.testline.get_components_by_type("DU")[0]
        if "Podman" in du_object.__class__.__name__:
            ru_sim_port_ids = (
                [str(du_object.ru_sim_port)]
                if ru_sim_port_ids is None
                else ru_sim_port_ids
            )
            ru_sim_instance_ids = (
                [du_object.ru_sim_instance_id]
                if ru_sim_instance_ids is None
                else ru_sim_instance_ids
            )
            for ru_sim_instance_id, ru_sim_port_id in zip(
                ru_sim_instance_ids, ru_sim_port_ids
            ):
                if du_object.kill_ru_sim_instance(ru_sim_instance_id, ru_sim_port_id):
                    logger.info(
                        f"RU Sim instance id - {ru_sim_instance_id} killed with port - {ru_sim_port_id} successfully!\n",
                        also_console=True,
                    )
                else:
                    raise FrameworkException(
                        f"RU Sim instance id - {ru_sim_instance_id} cannot be killed\n"
                    )
        else:
            raise FrameworkException("This keyword only supports for Podman!\n")

    def start_ru_sim_instance(
        self, ru_sim_instance_ids: list[str], component_id: str = None
    ) -> None:
        """
        Description:
            This function will Start RU Sim instance id with RU Sim port and verify it.
        Parameters:
            ru_sim_instance_id(list): The RU Sim instance id. Ex: ru_sim_instance_ids=["1", "2", "3", "4", "5"]
            id(str): component id. If id is None, then default will start first DU component.
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        try:
            if component_id is not None:
                du_object = self.testline.get_component_by_id(component_id)
            else:
                du_object = self.testline.get_components_by_type("DU")[0]

            if "Podman" in du_object.__class__.__name__:
                for ru_sim_instance_id in ru_sim_instance_ids:
                    logger.info(
                        f"Starting RU Sim instance id - {ru_sim_instance_id}",
                        also_console=True,
                    )
                    if du_object.start_ru_sim_instance(ru_sim_instance_id):
                        logger.info(
                            f"Started RU Sim instance id - {ru_sim_instance_id} successfully",
                            also_console=True,
                        )
                    else:
                        raise FrameworkException(
                            f"RU Sim instance id - {ru_sim_instance_id} cannot be started\n"
                        )
            else:
                raise FrameworkException("This keyword only supports for Podman!\n")
        except Exception as ex:
            raise FrameworkException(
                "Can not start RU Sim instance id with error:" + str(ex) + " occurred."
            )

    def trigger_rusim_alarm(
        self, component_id: str = None, ru_sim_instance_id: str = None
    ) -> None:
        """
        Description:
            This function will trigger FM notification
        Parameters:
            id(str): component id. If id is None, then default will start first component.
            ru_sim_instance_id(str): The RU Sim instance id. Ex: ru_sim_instance_id: 'ru_sim_1' , 'ru_sim_2',..
                                     If ru_sim_instance_id is None, then default will get ru_sim_instance_id=""ru_sim_1"" in yaml file.
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        try:
            if component_id is not None:
                du_object = self.testline.get_component_by_id(component_id)
            else:
                du_object = self.testline.get_components_by_type("DU")[0]

            if ru_sim_instance_id is None:
                ru_sim_instance_id = du_object.ru_sim_instance_id

            logger.info("Triggering FM notification", also_console=True)
            trigger_fm_notif_cmd = f"podman exec -w=/opt/gnb/mplane/rusimulator MPLANE ./trigger_FM_notif.sh {ru_sim_instance_id}"
            du_object.connection.sendCommand_shell(trigger_fm_notif_cmd)
            logger.info(
                f"====== FM Notification triggered with {ru_sim_instance_id} successfully\n"
            )
        except Exception as ex:
            raise FrameworkException(
                "Cannot trigger FM notification with error:" + str(ex) + " occurred."
            )

    def config_rrc_reconfig_fail(
        self, fail_type: str, delay: int = None, drop_cout: int = None, id: str = None
    ) -> None:
        """
        Description:
            Command to simulate the drop or delay scenario for rrc connection reconfig complete message for the specified ue id.
            If the failure type is set to drop, then rrc connetion reconfig complete is dropped for the times specifed by drop count. Drop count is required incase rrc connection reconfiguration message is retried by the network.
            Delay timer is used to delay the rrc connection reconfiguration complete message by amount of delay timer.
            To remove any failure setting for rrc connection reconfiguration message, then the failure type flag should be set to reset.
        Parameters:
            failure_type (str): type of failure 'drop' or 'delay'
            delay (int): time in milliseconds if failure type is delay
            drop count (int): in number if failure type is drop
            id (str): the UE ID.
        """
        if id is not None:
            ue = self.testline.get_component_by_id(id)
        else:
            logger.info(
                "====== No component id provided. So, The function config_rrc_reconfig_fail will be running on the first UE"
            )
            ue = self.testline.get_components_by_type("UE")[0]
            id = ue.id[0]
        ue.config_rrc_reconfig_fail(fail_type, delay, drop_cout, id)

    def add_cells_netconf_cmd(self, num_cells: int, config_file_name: str, id: str = None) -> bool:
        """
        Description:
            Change DU Cells on the fly without restarting components using the netconf commands
        Parameters:
            num_cells (int):        indicates number of cells DU should be brought up
            config_file_name (str): if modified it refers to the new config file
            id:                     The id of DU object (Eg. DU1). Otherwise, the first DU in yaml file will be used
        Returns:
            (Bool) : True if Output of debug cli commands matches with the corresponding template
            False if Output of debug cli commands does not match with the corresponding template
        """
        if id is not None:
            du_object = self.testline.get_component_by_id(id)
        else:
            du_object = self.testline.get_components_by_type("DU")[0]
        if du_object.add_cells_netconf_cmd(num_cells, config_file_name):
            logger.info(
                f"====== '{num_cells}' Cells successfully published on DU '{du_object.id}'",
                also_console=True,
            )
        else:
            raise FrameworkException(
                f"Some cells failed to be published on DU '{du_object.id}'"
            )

    def config_rrc_reconfig_fail_ho(
        self, fail_type: str, delay: int = None, drop_cout: int = None, id: str = None
    ) -> None:
        """
        Description:
            Command to simulate the drop or delay scenario for rrc configuration complete message towards target DU from UESim for the specified ue id.
            If the failure type is set to drop, then configuration complete is dropped for the times specifed by drop count.
            Delay timer is used to delay the configuration complete message by amount of delay timer.
            To remove any failure setting for configuration complete message, then the failure type flag should be set to reset.
        Parameters:
            failure_type (str): type of failure 'drop' or 'delay'
            delay (int): time in milliseconds if failure type is delay
            drop count (int): in number if failure type is drop
            id (str): the UE ID.
        """

        if id is not None:
            ue = self.testline.get_component_by_id(id)
        else:
            logger.info(
                "====== No component id provided. So, The function config_rrc_reconfig_fail_ho will be running on the first UE"
            )
            ue = self.testline.get_components_by_type("UE")[0]
            id = ue.id[0]
        ue.config_rrc_reconfig_fail_ho(fail_type, delay, drop_cout, id)

    def config_rach_fail_ho(
        self, fail_type: str, delay: int = None, drop_cout: int = None, id: str = None
    ) -> None:
        """
        Description:
            Command to simulate the drop or delay scenario for rach message towards target DU from UESim for the specified ue id.
            If the failure type is set to drop, then RACH message is dropped for the times specifed by drop count.
            Delay timer is used to delay the RACH message by amount of delay timer.
            To remove any failure setting for RACH message, then the failure type flag should be set to reset.
        Parameters:
            failure_type (str): type of failure 'drop' or 'delay'
            delay (int): time in milliseconds if failure type is delay
            drop count (int): in number if failure type is drop
            id (str): the UE ID.
        """
        if id is not None:
            ue = self.testline.get_component_by_id(id)
        else:
            logger.info(
                "====== No component id provided. So, The function config_rach_fail_ho will be running on the first UE"
            )
            ue = self.testline.get_components_by_type("UE")[0]
            id = ue.id[0]
        ue.config_rach_fail_ho(fail_type, delay, drop_cout, id)

    def send_traffic_bidirectional_pdu_session(
        self,
        ue_id: str,
        traffic_type: str,
        duration: int,
        interval: int,
        buffer_length: int,
        pdu_ips: str,
        ports: str,
        uplink_throughput: Optional[str] = None,
        downlink_throughput: Optional[str] = None,
        mss: Optional[str] = None,
    ) -> None:
        """
        Description:
            Sends bidirectional traffic with specific pdu session. The format of iperf report is Mbits (iperf -f m).
        Parameters:
            ue_id: The ID of the UE to send bidirectional traffic.
            traffic_type: The traffic type, TCP(Default)/UDP.
            duration: The time in seconds to transmit for. For iperf arg: -t
            interval: The interval time in seconds between periodic bandwidth report. For iperf arg: -i
            buffer_length: The buffer length to read or write in bytes. For iperf arg: -l
            pdu_ips: PDU Session IPs, can be one: ip1, or multiple PDU session IPs: [ip1, ip2, ...]
            ports: The port numbers for the traffic, can be 1 port: port1,  or multiple ports [port1, port2,...]
            uplink_throughput: The throughput for uplink traffic.
            downlink_throughput: The throughput for downlink traffic.
            mss: The maximum segment size for TCP traffic
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        ip_pattern = r"(\d+\.\d+\.\d+\.\d+)"
        pdu_ip_list = re.findall(ip_pattern, pdu_ips)

        port_pattern = r"(\d+)"
        port_list = re.findall(port_pattern, ports)

        logger.info(
            f"Send Traffic on PDU SESSION IP: {pdu_ip_list}, with PORT NUM: {port_list}",
            also_console=True,
        )

        ue = self.testline.get_component_by_id(ue_id)
        ret = ue.send_traffic_bidirectional_pdu_session(
            traffic_type,
            duration,
            interval,
            buffer_length,
            uplink_throughput,
            downlink_throughput,
            pdu_ip_list,
            port_list,
            mss,
            self.TL_name,
        )
        self.traffic_type = traffic_type

        # Raise exception if failed to sent traffic
        if not ret:
            raise Exception("Traffic sent failed, exiting")

    def start_traffic_pdu_session(
        self,
        traffic_type: str,
        direction: str,
        throughput: str,
        interval: int,
        buffer_length: int,
        pdu_ips: str,
        ports: str,
        core_id: Optional[str] = None,
        ue_id: Optional[str] = None,
        mss: Optional[str] = None,
    ) -> bool:
        """
        Description:
            Starts traffic with specific pdu session. The format of iperf report is Mbits (iperf -f m).
        Parameters:
            traffic_type (str): The traffic type, TCP(Default)/UDP.
            direction (str): The traffic direction, uplink/downlink.
            throughput (str): The Traffic bandwidth to send. For iperf arg: -b
            interval (int): The interval time in seconds between periodic bandwidth report. For iperf arg: -i
            buffer_length (int): The buffer length to read or write in bytes. For iperf arg: -l
            pdu_ips (str): PDU SESSION IP list
            ports (str): The port numbers list for the traffic. It can be one port if one PDU session,
                             or multiple ports if test multiple PDU sessions. For iperf arg: -p
            core_id (str): Core id that should be used in the traffic test
            ue_id (str): UE id that should be used in the traffic test
            mss (str, optional): The maximum segment size for TCP traffic. For iperf arg: -M
        Returns:
            traffic_started (bool): True if traffic started successfully
                                    False if traffic did not start successfully
        """
        ip_pattern = r"(\d+\.\d+\.\d+\.\d+)"
        pdu_ip_list = re.findall(ip_pattern, pdu_ips)

        port_pattern = r"(\d+)"
        port_list = re.findall(port_pattern, ports)

        if core_id is None:
            core_object = self.testline.get_components_by_type("CORE")[0]
        else:
            core_object = self.testline.get_component_by_id(core_id)
        if ue_id is None:
            ue = self.testline.get_components_by_type("UE")[0]
        else:
            ue = self.testline.get_component_by_id(ue_id)

        logger.info(
            f"Start Traffic on PDU SESSION IP: {pdu_ip_list}, with PORT NUM: {port_list}",
            also_console=True,
        )
        traffic_started = ue.start_traffic_pdu_session(
            traffic_type=traffic_type,
            direction=direction,
            throughput=throughput,
            interval=interval,
            buffer_length=buffer_length,
            pdu_ip_list=pdu_ip_list,
            port_list=port_list,
            core_object=core_object,
            mss=mss,
            TL_name=self.TL_name,
        )
        self.traffic_type = traffic_type
        if traffic_started:
            logger.info(
                "====== Sending traffic started successfully \n", also_console=True
            )
        else:
            raise Exception("Couldn't started traffic successfully\n")

    def stop_traffic_pdu_session(
        self, pdu_ips: str, direction: Optional[str] = None, ue_id: Optional[str] = None
    ) -> bool:
        """
        Description:
            This function will stops sending traffic with specific pdu session over the network.
        Parameters:
            ue_id: The id of the UE to start traffic on
            pdu_ips (str): PDU SESSION IP list
            direction (str): None is for bidirectional; uplink and downlink will be set up when input accordingly
            ue_id (str): UE id that should be used in the traffic test
        Returns:
            traffic_stopped (bool): True if traffic stopped successfully
                                    False if traffic did not stop successfully
        """
        if ue_id is None:
            ue = self.testline.get_components_by_type("UE")[0]
        else:
            ue = self.testline.get_component_by_id(ue_id)
        ip_pattern = r"(\d+\.\d+\.\d+\.\d+)"
        pdu_ip_list = re.findall(ip_pattern, pdu_ips)
        logger.info(f"Stop Traffic on UE ID: {pdu_ip_list}", also_console=True)
        traffic_stopped = ue.stop_traffic_pdu_session(pdu_ip_list, direction)
        if traffic_stopped:
            logger.info("====== Stop traffic successfully \n", also_console=True)
        else:
            raise Exception("Couldn't stopped traffic successfully\n")

    def start_traffic_multi_pdu_session(
        self,
        traffic_type: str,
        interval: int,
        buffer_length: int,
        pdu_ips: list,
        duration: int = None,
        port_ul_list: list = None,
        port_dl_list: list = None,
        uplink_throughput: str = None,
        downlink_throughput: str = None,
        ue_id: Optional[str] = None,
        mss: Optional[str] = None,
    ) -> None:
        """
        Description:
            Sends bidirectional traffic with specific pdu session. The format of iperf report is Mbits (iperf -f m).
        Parameters:
            traffic_type (str): The traffic type, TCP(Default)/UDP.
            interval (int): The interval time in seconds between periodic bandwidth report. For iperf arg: -i
            buffer_length (int): The buffer length to read or write in bytes. For iperf arg: -l
            pdu_ips (List[str]): multiple PDU session IPs
            duration (int): The time in seconds to transmit for
            port_ul_list (List[str]): The port numbers for UL traffic
            port_dl_list (List[str]): The port numbers for DL traffic
            uplink_throughput (str): The uplink Traffic bandwidth to send at
            downlink_throughput (str): The downlink Traffic bandwidth to send at
            ue_id (str): UE id that should be used in the traffic test
            mss (str, optional): The maximum segment size for TCP traffic
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        ip_pattern = r"(\d+\.\d+\.\d+\.\d+)"
        pdu_ip_list = re.findall(ip_pattern, pdu_ips)

        port_pattern = r"(\d+)"
        ul_ports = re.findall(port_pattern, port_ul_list) if port_ul_list else None
        dl_ports = re.findall(port_pattern, port_dl_list) if port_dl_list else None

        if ue_id is None:
            ue = self.testline.get_components_by_type("UE")[0]
        else:
            ue = self.testline.get_component_by_id(ue_id)

        logger.info(
            f"Send Traffic on PDU SESSION IP: {pdu_ip_list} with uplink iperf port NUM: {ul_ports} and with downlink iperf port NUM: {dl_ports}",
            also_console=True,
        )

        traffic_started = ue.start_traffic_multi_pdu_session(
            traffic_type,
            interval,
            buffer_length,
            pdu_ip_list,
            uplink_throughput,
            downlink_throughput,
            ul_ports,
            dl_ports,
            mss,
            duration,
            self.TL_name,
        )
        self.traffic_type = traffic_type

        # Raise exception if failed to sent traffic
        if traffic_started:
            logger.info(
                "====== Sending traffic started successfully \n", also_console=True
            )
        else:
            raise Exception("Couldn't started traffic successfully\n")

    def netconf_get_managed_element(self, component_id: str) -> list:
        """
        Description:
            This function will return a list of all <ManagedElement> via netconf-console
        Parameters:
            component_id: id of component object. EX: CUCP1/CUUP1/DU1
        Returns:
            me_list (list): list of all <ManagedElement>
        """

        logger.info(
            f"====== {component_id} - Get ManagedElement by netconf\n",
            also_console=True,
        )
        component = self.testline.get_component_by_id(component_id)
        netconf_alarmlist_cmd = (
            f"{Global_Variables.netconf_console_path}netconf-console "
            f"--host={component.oam_ip} "
            f"--port={Global_Variables.oam_port} "
            f"--user=netconf --privKeyType=rsa --privKeyFile={Global_Variables.NETCONF_PRIVATE_KEYPATH} "
            f"--get -x /ManagedElement"
        )

        netconf_alarm_output = self.send_command(
            component.id, netconf_alarmlist_cmd + "/ManagedElement"
        )

        # start processing the netconf command output
        tree = etree.fromstring(netconf_alarm_output.encode("utf-8"))
        # search the element with text=alarm_name
        me_list = tree.findall(".//3gpp_me:ManagedElement", self.namespaces)
        return me_list

    def get_alarm_list_from_me(self, me_list: list, id: int) -> list:
        """
        Description:
            From the me_list retreived from 'netconf_get_managed_element()', get the AlarmList of ManagedElement by ManagedElement's id
        Parameters:
            me_list: list of all <ManagedElement>
            id: <ManagedElement> id
        Returns:
            AlarmList (list): list of alarms in a <ManagedElement>
        """

        try:
            return me_list[id].find(".//3gpp_me:AlarmList", self.namespaces)
        except Exception as ex:
            raise Exception(str(ex))

    def validate_alarm(
        self,
        component_id: str,
        me_id: str,
        alarm_name: str,
        alarm_type: str,
        min_raised_time: datetime,
        max_raised_time: datetime,
        object_instance: str,
        perceived_severity: str,
        root_cause_indicator: str,
        ack_state: str,
        **optional_fields,
    ) -> list:
        """
        Description:
            Validate alarm as OAM's aspect, check the information of alarm. Specially, check attributes that are timezone.
            Validate only one alarm with the parameters as the expected information of alarm.
        Parameters:
            component_id: id of component object. EX: CUCP1/CUUP1/DU1
            me_id: <ManagedElement> id
            alarm_name: the expected name of alarm
            alarm_type: the expected type of alarm
            min_raised_time: the minimum time that the alarm must be raised
            max_raised_time: the maximum time that the alarm must be raised
            object_instance: the expected object instance of alarm
            perceived_severity: the expected perceived severity of alarm
            root_cause_indicator: the expected root cause indicator of alarm
            ack_state: the ack state of alarm
            **optional_fields: the others optional fields of alarm
        Returns:
            matching_alarms (list): list of alarms that are matched for the expected information
        """

        logger.info(f"====== {component_id} - Validate alarm:\n", also_console=True)
        me_list = self.netconf_get_managed_element(component_id)
        alarm_list = self.get_alarm_list_from_me(me_list, int(me_id))
        logger.info(f"The AlarmList of ManagedElement:\n {alarm_list}")
        alarm_records = alarm_list.findall(".//3gpp_me:alarmRecords", self.namespaces)

        actual_alarms = []
        for alarm in alarm_records:
            alarm_attribs = {}
            for field in alarm.iter():
                if field.tag.rfind("alarmName") > 0:
                    alarm_attribs[
                        field.tag.replace("{urn:dell:_3gpp-common-fm}", "")
                    ] = field.text
                elif not field.text.isspace():
                    alarm_attribs[
                        field.tag.replace(
                            "{urn:3gpp:sa5:_3gpp-common-managed-element}", ""
                        )
                    ] = field.text
            actual_alarms.append(alarm_attribs)

        logger.info(f"All the alarm records: {actual_alarms}")

        matching_alarms = []
        for alarm in actual_alarms:
            try:
                if alarm.get("alarmName") != alarm_name:
                    continue
                elif alarm.get("alarmType") != alarm_type:
                    continue
                elif alarm.get("objectInstance") != object_instance:
                    continue
                elif alarm.get("perceivedSeverity") != perceived_severity:
                    continue
                elif alarm.get("rootCauseIndicator") != root_cause_indicator:
                    continue
                elif alarm.get("ackState") != ack_state:
                    continue
                else:
                    alarm["alarmRaisedTime"] = self.convert_datetime_str(
                        alarm["alarmRaisedTime"]
                    )
                    min_raised_time = self.convert_datetime_str(min_raised_time)
                    max_raised_time = self.convert_datetime_str(max_raised_time)
                    if (
                        alarm["alarmRaisedTime"] > min_raised_time
                        and alarm["alarmRaisedTime"] < max_raised_time
                    ):
                        if self.check_optional_fields(alarm, **optional_fields):
                            matching_alarms.append(alarm)
                            logger.info(f"The matching alarm: {alarm}")
            except Exception as ex:
                logger.error(str(ex))
                return None
        return matching_alarms

    def validate_traffic_from_iperf(
        self,
        id: str,
        direction: str,
        expected_bw_range: str = None,
        expected_bw_range_ul: str = None,
        expected_bw_range_dl: str = None,
        pdu_ip: str = "",
        real_device: bool = False,
        graph_traffic: bool = False,
    ) -> None:
        """
        Description:
            validate the traffic through the iperf server log
        Parameters:
            id (str): the UE ID which want to be validated traffic from iperf log
            direction (str): the traffic direction to be validated: uplink or downlink
            expected_bw_range (str): expected throughput range for symmetric traffic: eg. 40-60
            expected_bw_range_ul (str): expected uplink throughput range for asymmetric traffic: eg. 40-60
            expected_bw_range_dl (str): expected downlink throughput range for asymmetric traffic: eg. 40-60
            pdu_ip (str): the PDU ip which needs to do traffic validation
            real_device (bool): whether the device is real or not
            graph_traffic (bool): whether to generate a traffic graph or not
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        logger.info("Validating Traffic", also_console=True, banner=True)
        uplink_ret = None
        downlink_ret = None
        UE = self.testline.get_component_by_id(id)
        core = self.testline.get_components_by_type("CORE")
        if isinstance(core, list) and len(core) > 0:
            core = core[0]
        # The file name will need to be updated for multi-ue test
        if pdu_ip:
            iperfsrv_logfile_ul = f"/tmp/iperf_srv_ul_{pdu_ip}_{self.TL_name}"
            iperfsrv_logfile_ul_err = None
            iperfsrv_logfile_dl = f"/tmp/iperf_srv_dl_{pdu_ip}_{self.TL_name}"
            iperfsrv_logfile_dl_err = None
            iperfcli_logfile_dl = f"/tmp/iperf_cli_dl_{pdu_ip}_{self.TL_name}"
            iperfcli_logfile_dl_err = None
            device_identifier = "pdu_" + pdu_ip
        elif real_device:
            iperfsrv_logfile_ul = f"/tmp/iperf_srv_ul_{id}_{self.TL_name}"
            iperfsrv_logfile_ul_err = f"/tmp/iperf_srv_ul_{id}_err_{self.TL_name}"
            iperfsrv_logfile_dl = (
                UE.laptop_log_path + f"iperf_srv_dl_{id}_{self.TL_name}"
            )
            iperfsrv_logfile_dl_err = (
                UE.laptop_log_path + f"iperf_srv_dl_{id}_err_{self.TL_name}"
            )
            iperf_local_file_dl = f"/tmp/iperf_srv_dl_{id}_{self.TL_name}"
            iperf_local_file_dl_err = f"/tmp/iperf_srv_dl_{id}_err_{self.TL_name}"
            device_identifier = id
        else:
            iperfsrv_logfile_ul = f"/tmp/iperf_srv_ul_{id}_{self.TL_name}"
            iperfsrv_logfile_ul_err = f"/tmp/iperf_srv_ul_{id}_err_{self.TL_name}"
            iperfsrv_logfile_dl = f"/tmp/iperf_srv_dl_{id}_{self.TL_name}"
            iperfsrv_logfile_dl_err = f"/tmp/iperf_srv_dl_{id}_err_{self.TL_name}"
            device_identifier = id
        if UE:
            if direction.lower() == "uplink":
                if UE.__class__.__name__ in ["BareMetalUE", "AndroidUE"]:
                    # In case of uplink, iperf server connection is the Core
                    iperf_template = "./framework/libraries/common/iperf3_srv.textFSM"
                    uplink_ret = self.log_manager.validate_tpt_from_iperf(
                        core.connection,
                        iperfsrv_logfile_ul,
                        iperfsrv_logfile_ul_err,
                        expected_bw_range,
                        iperf_template,
                        self.traffic_type,
                        Keywords.test_case_directory_path,
                        "uplink",
                        graph_traffic,
                        device_identifier,
                    )
                elif UE.__class__.__name__ in ["PodmanUESIM"]:
                    iperf_template = "./framework/libraries/common/iperf3_srv.textFSM"
                    # If traffic type is uplink or components are containerized, UE connection will work
                    uplink_ret = self.log_manager.validate_tpt_from_iperf(
                        UE.connection,
                        iperfsrv_logfile_ul,
                        iperfsrv_logfile_ul_err,
                        expected_bw_range,
                        iperf_template,
                        self.traffic_type,
                        Keywords.test_case_directory_path,
                        "uplink",
                        graph_traffic,
                        device_identifier,
                    )

            elif direction.lower() == "downlink":
                if UE.__class__.__name__ == "BareMetalUE":
                    # In case of downlink, iperf server connection is the UE
                    iperf_template = "./framework/libraries/common/iperf3_srv.textFSM"
                    if pdu_ip:
                        downlink_ret = self.log_manager.validate_tpt_from_iperf(
                            core.connection,
                            iperfsrv_logfile_dl,
                            iperfsrv_logfile_dl_err,
                            expected_bw_range,
                            iperf_template,
                            self.traffic_type,
                            Keywords.test_case_directory_path,
                            "downlink",
                            graph_traffic,
                            device_identifier,
                        )
                    elif not pdu_ip:
                        downlink_ret = self.log_manager.validate_tpt_from_iperf(
                            UE.connection,
                            iperfsrv_logfile_dl,
                            iperfsrv_logfile_dl_err,
                            expected_bw_range,
                            iperf_template,
                            self.traffic_type,
                            Keywords.test_case_directory_path,
                            "downlink",
                            graph_traffic,
                            device_identifier,
                        )
                elif UE.__class__.__name__ == "AndroidUE":
                    # In case of downlink, iperf server connection is the UE
                    iperf_template = "./framework/libraries/common/iperf3_srv.textFSM"
                    downlink_ret = self.log_manager.validate_tpt_from_iperf(
                        UE.connection,
                        iperfsrv_logfile_dl,
                        iperfsrv_logfile_dl_err,
                        expected_bw_range,
                        iperf_template,
                        self.traffic_type,
                        Keywords.test_case_directory_path,
                        "downlink",
                        graph_traffic,
                        device_identifier,
                        iperf_local_file_dl,
                        iperf_local_file_dl_err,
                    )
                elif UE.__class__.__name__ == "PodmanUESIM":
                    iperf_template = "./framework/libraries/common/iperf3_srv.textFSM"
                    # If traffic type is downlink or components are containerized, UE connection will work
                    if pdu_ip:
                        downlink_ret = self.log_manager.validate_tpt_from_iperf(
                            UE.connection,
                            iperfcli_logfile_dl,
                            iperfcli_logfile_dl_err,
                            expected_bw_range,
                            iperf_template,
                            self.traffic_type,
                            Keywords.test_case_directory_path,
                            "downlink",
                            graph_traffic,
                            device_identifier,
                        )
                    elif not pdu_ip:
                        downlink_ret = self.log_manager.validate_tpt_from_iperf(
                            UE.connection,
                            iperfsrv_logfile_dl,
                            iperfsrv_logfile_dl_err,
                            expected_bw_range,
                            iperf_template,
                            self.traffic_type,
                            Keywords.test_case_directory_path,
                            "downlink",
                            graph_traffic,
                            device_identifier,
                        )
            elif direction.lower() == "bidirectional":
                if pdu_ip:
                    iperf_ul_logfile = f"/tmp/iperf_ul_srv_bi_{pdu_ip}_{self.TL_name}"
                    iperf_ul_logfile_err = None
                    iperf_dl_logfile = f"/tmp/iperf_dl_srv_bi_{pdu_ip}_{self.TL_name}"
                    iperf_dl_logfile_err = None
                    device_identifier = "pdu_" + pdu_ip
                else:
                    iperf_ul_logfile = f"/tmp/iperf_ul_srv_bi_{id}_{self.TL_name}"
                    iperf_ul_logfile_err = (
                        f"/tmp/iperf_ul_srv_bi_{id}_err_{self.TL_name}"
                    )
                    iperf_dl_logfile = f"/tmp/iperf_dl_srv_bi_{id}_{self.TL_name}"
                    iperf_dl_logfile_err = (
                        f"/tmp/iperf_dl_srv_bi_{id}_err_{self.TL_name}"
                    )
                    device_identifier = id
                if UE.__class__.__name__ == "PodmanUESIM":
                    iperf_template = "./framework/libraries/common/iperf3_srv.textFSM"
                    # If traffic type is bidirectional or components are containerized, UE connection will work
                    #  Asymmetric traffic with different bidirectional bandwidth, only input expected_bw_range_ul & expected_bw_range_dl
                    if not expected_bw_range and (
                        expected_bw_range_ul and expected_bw_range_dl
                    ):
                        logger.info(
                            "Validating asymmetric traffic with different bidirectional bandwidth...",
                            also_console=True,
                        )
                        uplink_ret = self.log_manager.validate_tpt_from_iperf(
                            UE.connection,
                            iperf_ul_logfile,
                            iperf_ul_logfile_err,
                            expected_bw_range_ul,
                            iperf_template,
                            self.traffic_type,
                            Keywords.test_case_directory_path,
                            "uplink",
                            graph_traffic,
                            device_identifier,
                        )
                        downlink_ret = self.log_manager.validate_tpt_from_iperf(
                            UE.connection,
                            iperf_dl_logfile,
                            iperf_dl_logfile_err,
                            expected_bw_range_dl,
                            iperf_template,
                            self.traffic_type,
                            Keywords.test_case_directory_path,
                            "downlink",
                            graph_traffic,
                            device_identifier,
                        )
                    # Symmetric traffic with the same bidirectional bandwidth, only input expected_bw_range
                    elif expected_bw_range and not (
                        expected_bw_range_ul or expected_bw_range_dl
                    ):
                        logger.info(
                            "Validating symmetric traffic with the same bidirectional bandwidth...",
                            also_console=True,
                        )
                        uplink_ret = self.log_manager.validate_tpt_from_iperf(
                            UE.connection,
                            iperf_ul_logfile,
                            iperf_ul_logfile_err,
                            expected_bw_range,
                            iperf_template,
                            self.traffic_type,
                            Keywords.test_case_directory_path,
                            "uplink",
                            graph_traffic,
                            device_identifier,
                        )
                        downlink_ret = self.log_manager.validate_tpt_from_iperf(
                            UE.connection,
                            iperf_dl_logfile,
                            iperf_dl_logfile_err,
                            expected_bw_range,
                            iperf_template,
                            self.traffic_type,
                            Keywords.test_case_directory_path,
                            "downlink",
                            graph_traffic,
                            device_identifier,
                        )
                    else:
                        raise Exception(
                            "Wrong input for validating bidirectional traffic!",
                            also_console=True,
                        )
                elif UE.__class__.__name__ == "BareMetalUE":
                    iperf_template = "./framework/libraries/common/iperf3_srv.textFSM"
                    # If traffic type is bidirectional or components are containerized, UE connection will work
                    if pdu_ip:
                        uplink_ret = self.log_manager.validate_tpt_from_iperf(
                            core.connection,
                            iperf_ul_logfile,
                            iperf_ul_logfile_err,
                            expected_bw_range,
                            iperf_template,
                            self.traffic_type,
                            Keywords.test_case_directory_path,
                            "uplink",
                            graph_traffic,
                            device_identifier,
                        )
                        downlink_ret = self.log_manager.validate_tpt_from_iperf(
                            core.connection,
                            iperf_dl_logfile,
                            iperf_dl_logfile_err,
                            expected_bw_range,
                            iperf_template,
                            self.traffic_type,
                            Keywords.test_case_directory_path,
                            "downlink",
                            graph_traffic,
                            device_identifier,
                        )
                    elif not pdu_ip:
                        uplink_ret = self.log_manager.validate_tpt_from_iperf(
                            core.connection,
                            iperf_ul_logfile,
                            iperf_ul_logfile_err,
                            expected_bw_range,
                            iperf_template,
                            self.traffic_type,
                            Keywords.test_case_directory_path,
                            "uplink",
                            graph_traffic,
                            device_identifier,
                        )
                        downlink_ret = self.log_manager.validate_tpt_from_iperf(
                            UE.connection,
                            iperf_dl_logfile,
                            iperf_dl_logfile_err,
                            expected_bw_range,
                            iperf_template,
                            self.traffic_type,
                            Keywords.test_case_directory_path,
                            "downlink",
                            graph_traffic,
                            device_identifier,
                        )
                elif UE.__class__.__name__ == "AndroidUE":
                    if pdu_ip:
                        iperfsrv_ul_logfile = f"/tmp/iperf_{self.traffic_type}_ul_srv_bi_{pdu_ip}_{self.TL_name}"
                        iperfsrv_ul_logfile_err = None
                        iperfsrv_dl_logfile = f"/tmp/iperf_{self.traffic_type}_dl_srv_bi_{pdu_ip}_{self.TL_name}"
                        iperfsrv_dl_logfile_err = None
                    elif real_device:
                        iperfsrv_ul_logfile = f"/tmp/iperf_{self.traffic_type}_ul_srv_bi_{id}_{self.TL_name}"
                        iperfsrv_ul_logfile_err = f"/tmp/iperf_{self.traffic_type}_ul_srv_bi_{id}_err_{self.TL_name}"
                        iperfsrv_dl_logfile = (
                            UE.laptop_log_path
                            + f"iperf_{self.traffic_type}_dl_srv_bi_{id}_{self.TL_name}"
                        )
                        iperfsrv_dl_logfile_err = (
                            UE.laptop_log_path
                            + f"iperf_{self.traffic_type}_dl_srv_bi_{id}_err_{self.TL_name}"
                        )
                        iperf_local_file_dl = f"/tmp/iperf_{self.traffic_type}_dl_srv_bi_{id}_{self.TL_name}"
                        iperf_local_file_dl_err = f"/tmp/iperf_{self.traffic_type}_dl_srv_bi_{id}_err_{self.TL_name}"
                    else:
                        iperfsrv_ul_logfile = f"/tmp/iperf_{self.traffic_type}_ul_srv_bi_{id}_{self.TL_name}"
                        iperfsrv_ul_logfile_err = f"/tmp/iperf_{self.traffic_type}_ul_srv_bi_{id}_err_{self.TL_name}"
                        iperfsrv_dl_logfile = f"/tmp/iperf_{self.traffic_type}_dl_srv_bi_{id}_{self.TL_name}"
                        iperfsrv_dl_logfile_err = f"/tmp/iperf_{self.traffic_type}_dl_srv_bi_{id}_err_{self.TL_name}"
                    iperf_template = "./framework/libraries/common/iperf3_srv.textFSM"
                    # If traffic type is bidirectional or components are containerized, UE connection will work
                    if pdu_ip:
                        uplink_ret = self.log_manager.validate_tpt_from_iperf(
                            core.connection,
                            iperfsrv_ul_logfile,
                            iperfsrv_ul_logfile_err,
                            expected_bw_range,
                            iperf_template,
                            self.traffic_type,
                            Keywords.test_case_directory_path,
                            "uplink",
                            graph_traffic,
                            device_identifier,
                        )
                        downlink_ret = self.log_manager.validate_tpt_from_iperf(
                            core.connection,
                            iperfsrv_dl_logfile,
                            iperfsrv_dl_logfile_err,
                            expected_bw_range,
                            iperf_template,
                            self.traffic_type,
                            Keywords.test_case_directory_path,
                            "downlink",
                            graph_traffic,
                            device_identifier,
                            iperf_local_file_dl,
                            iperf_local_file_dl_err,
                        )
                    elif not pdu_ip:
                        # Asymmetric traffic with different bidirectional bandwidth, only input expected_bw_range_ul & expected_bw_range_dl
                        if not expected_bw_range and (
                            expected_bw_range_ul and expected_bw_range_dl
                        ):
                            logger.info(
                                "Validating asymmetric traffic with different bidirectional bandwidth...",
                                also_console=True,
                            )
                            uplink_ret = self.log_manager.validate_tpt_from_iperf(
                                core.connection,
                                iperfsrv_ul_logfile,
                                iperfsrv_ul_logfile_err,
                                expected_bw_range_ul,
                                iperf_template,
                                self.traffic_type,
                                Keywords.test_case_directory_path,
                                "uplink",
                                graph_traffic,
                                device_identifier,
                            )
                            downlink_ret = self.log_manager.validate_tpt_from_iperf(
                                UE.connection,
                                iperfsrv_dl_logfile,
                                iperfsrv_dl_logfile_err,
                                expected_bw_range_dl,
                                iperf_template,
                                self.traffic_type,
                                Keywords.test_case_directory_path,
                                "downlink",
                                graph_traffic,
                                device_identifier,
                                iperf_local_file_dl,
                                iperf_local_file_dl_err,
                            )
                        # Symmetric traffic with the same bidirectional bandwidth, only input expected_bw_range
                        elif expected_bw_range and not (
                            expected_bw_range_ul or expected_bw_range_dl
                        ):
                            logger.info(
                                "Validating symmetric traffic with the same bidirectional bandwidth...",
                                also_console=True,
                            )
                            uplink_ret = self.log_manager.validate_tpt_from_iperf(
                                core.connection,
                                iperfsrv_ul_logfile,
                                iperfsrv_ul_logfile_err,
                                expected_bw_range,
                                iperf_template,
                                self.traffic_type,
                                Keywords.test_case_directory_path,
                                "uplink",
                                graph_traffic,
                                device_identifier,
                            )
                            downlink_ret = self.log_manager.validate_tpt_from_iperf(
                                UE.connection,
                                iperfsrv_dl_logfile,
                                iperfsrv_dl_logfile_err,
                                expected_bw_range,
                                iperf_template,
                                self.traffic_type,
                                Keywords.test_case_directory_path,
                                "downlink",
                                graph_traffic,
                                device_identifier,
                                iperf_local_file_dl,
                                iperf_local_file_dl_err,
                            )
                        else:
                            raise Exception(
                                "Wrong input for validating bidirectional traffic!",
                                also_console=True,
                            )
                else:
                    raise Exception(
                        "Traffic type: 'bidirectional' is not supported for component {}!".format(
                            UE.__class__.__name__
                        )
                    )
            else:
                raise Exception(
                    "Traffic type: {} is not supported, it should be uplink, downlink or bidirectional!".format(
                        direction
                    )
                )

            if uplink_ret is False:
                logger.error("Uplink traffic validation failed")
            if downlink_ret is False:
                logger.error("Downlink traffic validation failed")
            if uplink_ret is False or downlink_ret is False:
                raise Exception("Traffic validation failed")
            else:
                logger.info(
                    "Traffic validation is done successfully!", also_console=True
                )
        else:
            logger.error(f"No UE found with ID '{id}'")

    def validate_traffic_from_iperf_multiple_ues(
        self, traffic_type: str, expected_bw_range: str, ue_ids: list
    ) -> None:
        """
        Description:
            Validate multiple UEs traffic through the iperf server log
        Parameters:
            traffic_type(str): the traffic type to be validated: uplink|downlink
            expected_bw_range(str): expected throughput range with -: eg. 40-60
            ue_ids (list): The list of start_ue and stop_ue want to validated traffic from iperf log
                E.g. ue_ids: [1,5] -> UE ID: 1,2,3,4,5
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        logger.info("Validating Multiple UEs' Traffic", also_console=True, banner=True)
        start_ue_id = ue_ids[0]
        stop_ue_id = ue_ids[1]
        for ue_id in range(start_ue_id, stop_ue_id + 1):
            logger.info(f"Validate traffic of UE ID: {ue_id}", also_console=True)
            self.validate_traffic_from_iperf(
                f"UE{ue_id}", traffic_type, expected_bw_range
            )

    def validate_traffic_from_iperf_multi_pdu(
        self, id: str, direction: str, expected_bw_range: str, pdu_ips: str
    ) -> None:
        """
        Description:
            Validate multiple PDU sessions traffic through the iperf server log
        Parameters:
            id (str): the UE ID which want to be validated traffic from iperf log
            direction (str): the traffic direction to be validated: upli nk|downlink
            expected_bw_range (str): expected throughput range with -: eg. 40-60
            pdu_ips (str): The list of PDU SESSION IP to do traffic validation from iperf log: eg. [ip1, ip2]
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        ip_pattern = r"(\d+\.\d+\.\d+\.\d+)"
        pdu_ip_list = re.findall(ip_pattern, pdu_ips)

        for pdu_ip in pdu_ip_list:
            logger.info(
                f"Validate Traffic on PDU SESSION IP: {pdu_ip}", also_console=True
            )
            self.validate_traffic_from_iperf(
                id, direction, expected_bw_range, pdu_ip=pdu_ip
            )

    def check_optional_fields(self, alarm: dict, **optional_fields: dict) -> bool:
        for key, value in optional_fields.items():
            if key in alarm.keys() and alarm[key] == value:
                continue
            else:
                return False
        return True

    def convert_datetime_str(self, time_str: str) -> datetime:
        logger.info(f"Converting {time_str}")
        try:
            time = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S%z")
            logger.info(f"Timezone is {time.tzinfo}")
            logger.info(f"Time after format is {time}")
            return time
        except Exception:
            logger.warn("Trying a different date format.")

        try:
            time = parser.parse(time_str)
            logger.info(f"Timezone {time.tzinfo}")
            return time
        except Exception:
            raise AssertionError(f"Invalid date format: {time_str}")

    def check_5gc_health(self, id: str = None, scenario: str = None, restart: bool = False) -> None:
        """
        Description:
            This keyword checks 5G core health through multiple checks like ping check, state check, etc.
        Parameters:
            id: CORE id from yaml file
            scenario: takes input from user about which scenario needs to run and loads the path accordingly
            restart: used to restart core if health check fails
        """
        try:
            logger.info("Checking Viavi 5GC health", also_console=True, banner=True)

            cucps = self.testline.get_components_by_type("CUCP")
            cucp_n2_ips = []
            for cucp in cucps:
                if hasattr(cucp, "n2_ip"):
                    cucp_n2_ips.append(cucp.n2_ip)

            if id:
                core_object = self.testline.get_component_by_id(id)
                core_object.health_check(scenario, cucp_n2_ips, restart)
            else:
                core_objects = self.testline.get_components_by_classname("TeraVmCore")
                for core in core_objects:
                    core.health_check(scenario, cucp_n2_ips, restart)
        except Exception as exc:
            logger.error(exc)
            raise exc

    def summarize_mcs_sweep_results(self, direction: str, imcs_list: List[int]) -> None:
        """
        Description:
            Reads robot output.xml and summarizes the BLER and SNR values in a text file
        Parameters:
            direction(str)       : either ul or dl
            imcs_list(List[int]) : list of mcs indices to write
        Returns
        """
        file_name = "output.xml"
        for dir in os.listdir(Keywords.test_suite_directory_path):
            if "utput.xml" in dir:  # to handle other names, e.g., Agent-Output.xml
                file_name = dir
                break

        with open(
            os.path.join(Keywords.test_suite_directory_path, file_name), "r"
        ) as input, open(
            os.path.join(Keywords.test_suite_directory_path, "mcs_sweep_summary.txt"),
            "w",
        ) as output:
            log = input.read()
            txrate_list = re.findall(r"bw_average: \d+.\d+", log)
            rxloss_list = re.findall(r"Total packet loss.*:\d+[\.\d+]*", log)
            bler_list = re.findall(r"bler value.*", log)
            if direction == "DL":
                snr_regex = r"sinr packet.*\[.*\]"
                snr_base = 46  # For thresholds, the actual value is (IE value – 46) / 2 dB (see SINR-Range from 3GPP TS 38.331)
            else:
                snr_regex = r"'PUSCH-SNR': .*\[.*\]"
                snr_base = 128  # The actual value is (value – 128) / 2 dB, ask Timor or Anirudh
            sinr_list = re.findall(snr_regex, log)

            output.write("I_MCS\tRx (mbps)\tLoss(%)\t\tBLER(%)\t\tSNR (dB)\n")
            for i_mcs in range(len(imcs_list)):
                output.write(
                    "%s\t%6.2f\t\t%6.2f\t\t%6.2f\t\t%6.2f\n"
                    % (
                        imcs_list[i_mcs],
                        float(re.search(r"\d+.\d+", txrate_list[i_mcs]).group(0)),
                        float(re.search(r"\d+[\.\d+]*", rxloss_list[i_mcs]).group(0)),
                        float(re.search(r"\d+.\d+", bler_list[i_mcs]).group(0)),
                        (
                            mean(list(map(int, re.findall(r"\d+", sinr_list[i_mcs]))))
                            - snr_base
                        )
                        / 2.0,
                    )
                )

    def get_ru_status(self, ru_id: str = None) -> str:
        """
        Description:
            Keyword to check the status of GenericRU
        Parameters:
            ru_id (str): ID of the radio, which is defined in yaml file (exmaple: RU1)
        Returns:
            ru_status (str): running, or stopped
        """
        radios = self.testline.get_components_by_classname("GenericRU")
        ru_status = ""
        if not radios:
            logger.error("Keyword get_ru_status only supports the GenericRU now.")
            return

        if ru_id is None:
            for radio in radios:
                ru_status += f"Status of RU {radio} is: {radio.status()} \n"
        else:
            radio = self.testline.get_component_by_id(ru_id)
            ru_status = f"Status of RU {ru_id} is: {radio.status()}"
        return ru_status

    def load_variables_by_json_key(self, tag, configuration_path):
        """
        Description: Reads configuration_path.json file and creates Suite and test variables according to tag names
        and location defined in Json Json config should have tag names in lower case. Hierarchy of variable
        definitions from lowest to highest (higher the number ,the more priority it will get for being set 1. Tag
        defined on a global level. 2. Tag defined on a suite level. 3. Tags defined on a test level. If a Tag has the
        same name in both global level and test level. The test level value will be set.
            Parameters:
                tag(str)       : Tag that will be referenced in the json file
                configuration_path(str) : path location of json file.
            Returns
        """
        try:
            # Opening JSON file
            f = open(configuration_path)
        except Exception as e:
            raise Exception(f"Unable to open file {configuration_path} due to: {e}")

        data = json.load(f)

        suite_name = BuiltIn().get_variable_value("$SUITE_NAME")
        # extract suite name from full suite name path
        suite_name = suite_name.split(".")
        suite_name = suite_name[len(suite_name) - 1]
        test_name = BuiltIn().get_variable_value("$TEST_NAME")
        logger.info(f"suite: {BuiltIn().get_variable_value('$SUITE_NAME')}")
        logger.info(f"test: {BuiltIn().get_variable_value('$TEST_NAME')}")

        # Check if Suite configuration exists
        if data.get(suite_name):
            # check if tag exists in Suite and test_names config
            if data[suite_name].get(test_name) and data[suite_name][test_name].get(tag):
                # Check if Suite and tag are dict
                if isinstance(data[suite_name][test_name][tag], dict):
                    key_list = list(data[suite_name][test_name][tag].keys())
                    val_list = list(data[suite_name][test_name][tag].values())

                    for i in range(0, len(val_list)):
                        BuiltIn().set_test_variable(
                            "${" + key_list[i].upper() + "}", val_list[i]
                        )
                        logger.info(
                            f"Robot test variable set key ={key_list[i]}, value ={val_list[i]}"
                        )
                else:
                    BuiltIn().set_test_variable(
                        "${" + tag.upper() + "}", data[suite_name][test_name][tag]
                    )
                    logger.info(
                        f"Robot test variable set key ={tag}, value ={data[suite_name][test_name][tag]}"
                    )

            # check if tag exists in Suite config
            elif data[suite_name].get(tag):
                # Check if Suite and tag are dict
                if isinstance(data[suite_name][tag], dict):
                    key_list = list(data[suite_name][tag].keys())
                    val_list = list(data[suite_name][tag].values())

                    for i in range(0, len(val_list)):
                        BuiltIn().set_suite_variable(
                            "${" + key_list[i].upper() + "}", val_list[i]
                        )
                        logger.info(
                            f"Robot suite variable set key ={key_list[i]}, value ={val_list[i]}"
                        )
                else:
                    BuiltIn().set_suite_variable(
                        "${" + tag.upper() + "}", data[suite_name][tag]
                    )
                    logger.info(
                        f"Robot suite variable set key ={tag}, value ={data[suite_name][tag]}"
                    )
        # check if tag exists in config
        elif data.get(tag):
            # Check if tag is dict
            if isinstance(data[tag], dict):
                key_list = list(data[tag].keys())
                val_list = list(data[tag].values())

                for i in range(0, len(val_list)):
                    BuiltIn().set_suite_variable(
                        "${" + key_list[i].upper() + "}", val_list[i]
                    )
                    logger.info(
                        f"Robot suite variable set key ={key_list[i]}, value ={val_list[i]}"
                    )
            else:
                BuiltIn().set_suite_variable("${" + tag.upper() + "}", data[tag])
                logger.info(f"Robot suite variable set key ={tag}, value ={data[tag]}")

        # Closing file
        f.close()

    def wait(
        self,
        wait_time: str,
        message: str = None,
        ue_id: str = "",
        health_check: str = False,
        interval: int = 30,
        no_of_pings: int = 5,
        threshold: int = 1,
    ) -> None:
        """
        Description:
            Allows to add wait into test with custom message that will be printed to console
        Parameters:
            wait_time(String)       : amount of time in seconds to wait in test
            message(String)         : Allows to pass in custom message
            ue_id(String)           : The UE id that heath check will run on.
            health_check(Boolean)  : Will enable health check if true
            interval(int)          :Value in seconds for interval of health check
            no_of_pings(int)       :Number of pings being sent to validate connection
            threshold(int)         :Number of pings that have to pass in order to validate the connection
        does not return value
        """

        logger.info(
            f"====== wait: Ping threshold set to  {threshold}"
        )
        if message:
            logger.info(
                f"{message} (wait ={str(wait_time)} seconds).", also_console=True
            )
        else:
            logger.info(f"Waiting {str(wait_time)} seconds.", also_console=True)

        # We will create loop with health check interval
        # Formula ( wait time  /  (healthcheck interval = (healthcheck time + wait))
        # Example: Wait:600 / interval:10 (ping and ip check: 4 + wait:6) values in seconds

        if health_check and wait_time and ue_id:
            check_time = no_of_pings + 1
            if interval <= check_time:
                interval = check_time
                logger.info(
                    f"Interval parameter value of Wait keyword is to low. Setting new interval time to {interval}",
                    also_console=True,
                )
            loop_value = int(wait_time) / int(interval)
            remaining_time = int(wait_time) % int(interval)
            # Run required loops
            for loop_interval in range(0, int(loop_value)):
                self.check_ue_connection_health(int(no_of_pings), threshold=threshold, ue_id=ue_id)
                time.sleep(int(interval) - int(check_time))
            # Run the remainder of the seconds
            self.check_ue_connection_health(
                int(no_of_pings), threshold=int(threshold), ue_id=ue_id
            )
            time.sleep(remaining_time)
        else:
            time.sleep(int(wait_time))
        logger.info("Wait has completed.", also_console=True)

    def check_ue_connection_health(
        self, no_of_pings: int = 3, threshold: int = None, ue_id=None
    ) -> None:
        """
        Description:
            This method is for checking the health of the UE connection to the GnB.
            This is done by checking if ip had changed since attach and by sending pings to the core.
        """
        # Check if ip changed
        if ue_id:
            component_obj = self.testline.get_component_by_id(ue_id)
            if not component_obj.ue_ip_change_check(component_obj):
                raise Exception(
                    "Ip of UE has changed since attach, Indicating possible detach",
                    also_console=True,
                )
            self.send_ping("UE", "core", id=ue_id, threshold=threshold)

    def config_reestab_comp_fail(
        self, fail_type: str, delay: int = None, drop_count: int = None, id: str = None
    ) -> None:
        """
        Description:
            Command to simulate the drop or delay scenario for RRC Reestablishment Complete for the specified ue id.
            If the failure type is set to drop, then RRC Reestablishment Complete message is dropped for the times specifed by drop count.
            Delay timer is used to delay the RRC Reestablishment Complete message by amount of delay timer.
            To remove any failure setting for RRC Reestablishment Complete message, then the failure type flag should be set to reset.
        Parameters:
            failure_type (str): type of failure 'drop', 'delay' or 'reset'
            delay (int): time in milliseconds if failure type is delay
            drop count (int): number if failure type is drop
            id (str): the UE ID.
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        if id is not None:
            ue = self.testline.get_component_by_id(id)
        else:
            logger.info(
                "====== No component id provided. So, The function config_reestab_comp_fail will be running on the first UE"
            )
            ue = self.testline.get_components_by_type("UE")[0]
            id = ue.id[0]
        ue.config_reestab_comp_fail(fail_type, delay, drop_count, id)

    def start_QXDM_logging(
        self,
        id: str = None,
        timeout: int = None,
        dmc_file: str = "DEFAULT",
    ) -> None:
        """
        Description:
            This function will load QUTS script to Android UE and start to collect QXDM logs by running script.
        Parameter:
            id (str): The ue id, if none is set will do for all ue ids on the Test Line. Default value is None.
            timeout (int): Default to None, only for testing which takes under 10 hours. If testing is over 10 hours, set timeout.
            dmc_file (str): DMC file path. Defaults to "DEFAULT" (default filters in get_qxdm_log script).
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        logger.info("Starting QXDM Logging", also_console=True, banner=True)
        try:
            if id is not None:
                ue = self.testline.get_component_by_id(id)
                ue.start_QXDM_logging(timeout, dmc_file)
            else:
                ue_components = self.testline.get_components_by_type("UE")
                for ue in ue_components:
                    ue.start_QXDM_logging(timeout, dmc_file)
        except Exception as e:
            raise FrameworkException(f"Start QXDM Logging failed due to {e}")

    def stop_QXDM_logging(self, id: str = None) -> None:
        """
        Description:
            This function will stop to collect QXDM logs.
        Parameter:
            id (str): The ue id, if none is set will do for all ue ids on the Test Line. Default value is None.
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        if id is not None:
            ue = self.testline.get_component_by_id(id)
            ue.stop_QXDM_logging()
        else:
            ue_components = self.testline.get_components_by_type("UE")
            for ue in ue_components:
                ue.stop_QXDM_logging()

    def send_ping(
        self,
        source: str,
        destination: str,
        no_of_pings: int = 3,
        length: int = None,
        threshold: int = None,
        id: str = None,
        destination_id: str = None,
    ) -> None:
        """
        Description:
            Pings various components to check reachability
        Parameters:
            source: Source from which ping needs to be initiated -only UE is supported currently as a source
            destination: component which needs to be pinged
            no_of_pings: total number of pings to be transmitted
            length: ping length to be transmitted
            threshold: minimum packets to be received in order to pass the test case. If not specified, threshold is the number of pings sent
            id (str): The id of UE object. Ex: UE1.
            destination_id (str): The id of component wanted to send ping to. EX: DU1,...
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        destination_ip = ""
        if id is not None:
            UE = self.testline.get_component_by_id(id)
        else:
            UE = self.testline.get_components_by_type("UE")[0]
        if destination == "core":
            destination_ip = UE.iperf_dest
        if destination == "du":
            if destination_id is not None:
                DU = self.testline.get_component_by_id(destination_id)
            else:
                DU = self.testline.get_components_by_type("DU")[0]
            destination_ip = DU.ip
        if destination == "cu":
            if destination_id is not None:
                CUCP = self.testline.get_component_by_id(destination_id)
            else:
                CUCP = self.testline.get_components_by_type("CUCP")[0]
            destination_ip = CUCP.ip
        ping_check = False
        if source == "UE":
            try:
                ping_check = UE.send_ping(
                    destination_ip, no_of_pings, length, threshold
                )
            except Exception as e:
                logger.error(
                    f"Ping check failed due to {str(e)}",
                )

        if not ping_check:
            raise Exception("====== Ping check failed\n")

    def get_interface_name(self, *interfaces: str) -> dict:
        """
        Description:
            This function helps to get the interface names for the interfaces in a TL. The current supported
            interfaces are F1-C, E1, N2.
        Parameter:
            interfaces (str): The list of interfaces for which we need to fetch the interface name from the TL
        Returns:
            A dictionary will be returned for all interfaces requested. The "interface-name_component" will be
            the key and the "interface-name" will be its value.
        """
        interfaces_dict = {}
        for interface in interfaces:
            if interface.lower() == "f1c":
                interface_in_xml = "EP_F1C"
                for du_component in self.testline.get_components_by_type("DU"):
                    f1c_interface_du = du_component.fetch_interface_name(
                        interface_in_xml
                    )
                    logger.info(
                        f"The interface name for F1-C interface from the DU - {du_component.id} side is: {f1c_interface_du}",
                        also_console=True,
                    )
                    interfaces_dict[
                        f"{interface}_DU_{du_component.id}"
                    ] = f1c_interface_du
                for cucp_component in self.testline.get_components_by_type("CUCP"):
                    f1c_interface_cucp = cucp_component.fetch_interface_name(
                        interface_in_xml
                    )
                    logger.info(
                        f"The interface name for F1-C interface from the CUCP - {cucp_component.id} side is: {f1c_interface_cucp}",
                        also_console=True,
                    )
                    interfaces_dict[
                        f"{interface}_CUCP_{cucp_component.id}"
                    ] = f1c_interface_cucp
            elif interface.lower() == "n2":
                interface_in_xml = "EP_NgC"
                for cucp_component in self.testline.get_components_by_type("CUCP"):
                    n2_interface_cucp = cucp_component.fetch_interface_name(
                        interface_in_xml
                    )
                    logger.info(
                        f"The interface name for N2 interface from the CUCP - {cucp_component.id} side is: {n2_interface_cucp}",
                        also_console=True,
                    )
                    interfaces_dict[
                        f"{interface}_CUCP_{cucp_component.id}"
                    ] = n2_interface_cucp
                for core_component in self.testline.get_components_by_type("CORE"):
                    n2_interface_core = core_component.fetch_interface_name(
                        interface_in_xml
                    )
                    if n2_interface_core is not None:
                        logger.info(
                            f"The interface name for N2 interface from the CORE - {core_component.id} side is: {n2_interface_core}",
                            also_console=True,
                        )
                    else:
                        logger.info(
                            "The inventory file does not have the N2 IP defined for the AMF, hence we cannot fetch "
                            f"the N2 interface name from the CORE - {core_component.id} side",
                            also_console=True,
                        )
                    interfaces_dict[
                        f"{interface}_CORE_{core_component.id}"
                    ] = n2_interface_core
            elif interface.lower() == "e1":
                interface_in_xml = "EP_E1"
                for cucp_component in self.testline.get_components_by_type("CUCP"):
                    e1_interface_cucp = cucp_component.fetch_interface_name(
                        interface_in_xml
                    )
                    logger.info(
                        f"The interface name for E1 interface from the CUCP - {cucp_component.id} side is: {e1_interface_cucp}",
                        also_console=True,
                    )
                    interfaces_dict[
                        f"{interface}_CUCP_{cucp_component.id}"
                    ] = e1_interface_cucp
                for cuup_component in self.testline.get_components_by_type("CUUP"):
                    e1_interface_cuup = cuup_component.fetch_interface_name(
                        interface_in_xml
                    )
                    logger.info(
                        f"The interface name for E1 interface from the CUUP - {cuup_component.id} side is: {e1_interface_cuup}",
                        also_console=True,
                    )
                    interfaces_dict[
                        f"{interface}_CUUP_{cuup_component.id}"
                    ] = e1_interface_cuup
            else:
                raise FrameworkException(
                    "This keyword currently only supports interfaces F1C, N2, E1. Please retry for these "
                    "interfaces only"
                )
        return interfaces_dict

    def connect_attero_device(self, id: str = None) -> None:
        """
        Description:
            Connect to AtteroX device
        Parameters:
            id: the id for atteroX device that is predefined in the TL yaml file by default its None
                so it get all attero connected to the TL
        Returns:
            None
        Raises:
            FrameworkException: If connection to AtteroX device fails.
        """
        if id:
            Atteros = [self.testline.get_component_by_id(id)]
        else:
            Atteros = self.testline.get_components_by_type("AtteroX")
        for Attero in Atteros:
            try:
                Attero.start()
            except Exception as exc:
                raise FrameworkException(
                    f"Couldn't connect to attero device with id '{Attero.id}'. The following error occured: {exc}"
                )

    def disconnect_attero_device(self, id: str = None) -> None:
        """
        Description:
            Disconnect to AtteroX device
        Parameters:
            id: the id for atteroX device that is predefined in the TL yaml file by default its None
                so it get all attero connected to the TL
        Returns:
            None
        Raises:
            FrameworkException: If disconnection to AtteroX device fails.
        """
        if id:
            Atteros = [self.testline.get_component_by_id(id)]
        else:
            Atteros = self.testline.get_components_by_type("AtteroX")
        for Attero in Atteros:
            try:
                Attero.stop()
            except Exception as exc:
                raise FrameworkException(
                    f"Couldn't disconnect to attero device with id '{Attero.id}'. The following error occured: {exc}"
                )

    def set_attero_delay(
        self, port: int, flow: int, delay: Union[int, float], id: str = None
    ) -> None:
        """
        Description:
            Set fixed delay for a specific port and flow.
        Parameters:
            port (int): The port number.
            flow (int): The flow number.
            delay (Union[int, float]): The delay value to be set.
            id: the id for atteroX device that is predefined in the TL yaml file by default its None
                so it get all attero connected to the TL
        Returns:
            None
        Raises:
            FrameworkException: If setting the delay fails.
        """
        if id:
            Atteros = [self.testline.get_component_by_id(id)]
        else:
            Atteros = self.testline.get_components_by_type("AtteroX")
        for Attero in Atteros:
            try:
                logger.info(
                    f"Setting fixed delay of {delay} for AtteroX with id '{Attero.id}'"
                )
                Attero.exec_atteroset_cmd(
                    f"Impair ImpairProfile #{port} #{flow} FixedDelay {delay}"
                )
                logger.info(
                    f"Fixed delay of {delay} is set for AtteroX with id '{Attero.id}'"
                )
            except Exception as exc:
                raise FrameworkException(
                    f"Couldn't set delay for AtteroX with id '{Attero.id}'. The following error occured: {exc}"
                )

    def set_attero_instrinsics_mode(self, mode: int, id: str = None) -> None:
        """
        Description:
            Set low intrinsic mode for AtteroX device.
        Parameters:
            mode (int): The mode value to be set.
            id: the id for atteroX device that is predefined in the TL yaml file by default its None
                so it get all attero connected to the TL
        Returns:
            None
        Raises:
            FrameworkException: If setting the low intrinsic mode fails.
        """
        if id:
            Atteros = [self.testline.get_component_by_id(id)]
        else:
            Atteros = self.testline.get_components_by_type("AtteroX")
        for Attero in Atteros:
            try:
                logger.info(
                    f"Setting low instrinsic mode of AtteroX device for AtteroX with id '{Attero.id}'"
                )
                Attero.exec_atteroset_cmd(
                    f"Impair MemoryAllocation LowInstrinsicsModeEnable {mode}"
                )
                logger.info(
                    f"Low instrinsic mode set for AtteroX with id '{Attero.id}'"
                )
            except Exception as exc:
                raise FrameworkException(
                    f"Couldn't set low instrinsic mode for AtteroX with id '{Attero.id}'. The following error occured: {exc}"
                )

    def start_impairment_attero(self, id: str = None) -> None:
        """
        Description:
            Start impairment on AtteroX device
        Parameters:
            id: the id for atteroX device that is predefined in the TL yaml file by default its None
                so it get all attero connected to the TL
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        if id:
            Atteros = [self.testline.get_component_by_id(id)]
        else:
            Atteros = self.testline.get_components_by_type("AtteroX")
        for Attero in Atteros:
            try:
                logger.info(f"Start impairment on AtteroX device with id '{Attero.id}'")
                Attero.start_impairment()
                logger.info(
                    f"Impairment has been started on AtteroX device with id '{Attero.id}'"
                )
            except Exception as exc:
                raise FrameworkException(
                    f"Couldn't start impairment on AtteroX device with id '{Attero.id}'. The following error occured: {exc}"
                )

    def stop_impairment_attero(self, id: str = None) -> None:
        """
        Description:
            Stop impairment on AtteroX device
        Parameters:
            id: the id for atteroX device that is predefined in the TL yaml file by default its None
                so it get all attero connected to the TL
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        if id:
            Atteros = [self.testline.get_component_by_id(id)]
        else:
            Atteros = self.testline.get_components_by_type("AtteroX")
        for Attero in Atteros:
            try:
                logger.info(f"Stop impairment on AtteroX device with id '{Attero.id}'")
                Attero.stop_impairment()
                logger.info(
                    f"Impairment has been stopped on AtteroX device with id '{Attero.id}'"
                )
            except Exception as exc:
                raise FrameworkException(
                    f"Couldn't stop impairment on AtteroX device with id '{Attero.id}'. The following error occured: {exc}"
                )

    def set_attero_rate(self, flow: int, percentage: float, id: str = None) -> None:
        """
        Description:
            Set Attero Packet Corruption Lost Rate percentage.
            Manual steps:
            Click to Port1->Port2
            -> Choose Fixed Delay and Jitter
            -> Enable Lost option
            -> Fill in Rate (%)
            -> Click apply change
            -> Apply same steps for Port2->Port1
            Keyword sends Attero command "atteroset Impair Corruption # Lost Distribution Percent" to be executed on Attero side.
            The command simulates the above manual GUI steps.
        Parameters:
            flow (int): flow number(Port1 -> Port2 OR Port2 -> Port1)
            percentage (float): set the lost rate percentage to the given value
        Returns:
            None: this method only automates the above manual steps.
        Raises:
            FrameworkException:  If the execution of the command fails.
        """
        if id:
            Atteros = [self.testline.get_component_by_id(id)]
        else:
            Atteros = self.testline.get_components_by_type("AtteroX")
        for Attero in Atteros:
            try:
                logger.info(
                    f"Setting Lost packets rate {percentage} for AtteroX with id '{Attero.id}'"
                )
                Attero.set_impair_corruption_lost_percent(flow, percentage)
                new_attero_rate = Attero.exec_atteroget_cmd(f"Impair Corruption #{flow} Lost Distribution Percent")
                logger.info(
                    f"Lost packets rate is set to {new_attero_rate} for AtteroX with id '{Attero.id}'"
                )
            except Exception as exc:
                raise FrameworkException(
                    f"Couldn't set Lost packets rate for AtteroX with id '{Attero.id}'. The following error occured: {exc}"
                )

    def configure_link_corruption(self, port: int, state: int, id: str = None) -> None:
        """
        Description:
            configure link corruption state
        Parameter:
            port (int): the port need to be Set link corruption on it
            state (int): the State of link corruption on specified port
            id: the id for atteroX device that is predefined in the TL yaml file by default its None
                so it get all attero connected to the TL
        Returns:
            None. The method set the state of link corruption on specific port (so, there will be no return value).
        """
        if id:
            Atteros = [self.testline.get_component_by_id(id)]
        else:
            Atteros = self.testline.get_components_by_type("AtteroX")
        for Attero in Atteros:
            try:
                logger.info(
                    f"Configuring link corruption with Enable state: {state} for AtteroX with id '{Attero.id}'"
                )
                Attero.exec_atteroset_cmd(
                    f"Impair Corruption Physical #{port} Enable {state}"
                )
                logger.info(
                    f"Configured Link Corruption with Enable state of {state} Successfully for AtteroX with id '{Attero.id}'"
                )
            except Exception as exc:
                raise FrameworkException(
                    f"Couldn't configure the Link Corruption for AtteroX with id '{Attero.id}'. The following error occured: {exc}"
                )

    def deactivate_ru_carriers(self) -> None:
        logger.info("====== Deactivating the RU carriers", also_console=True)
        self.configure_component(
            "RU", config_file="resources/netconf/deactivate_carriers_foxconn_ru.xml"
        )
        # Check whether the RU carrier state is disabled
        disable_status = self.RU.get_state(
            "/user-plane-configuration/tx-array-carriers/state", "DISABLED"
        )
        if disable_status:
            logger.info("====== RU carriers state is disabled\n", also_console=True)
        else:
            raise Exception("Disabled state cannot be verified for RU carriers")

    def activate_ru_carriers(self) -> None:
        logger.info("====== Activating the RU carriers", also_console=True)
        self.configure_component(
            "RU", config_file="resources/netconf/activate_carriers_foxconn_ru.xml"
        )
        # Check whether the RU carrier state is enabled
        ru_status = self.RU.get_state(
            "/user-plane-configuration/tx-array-carriers/state", "READY"
        )
        if ru_status:
            logger.info("====== RU carriers state is enabled\n", also_console=True)
        else:
            raise Exception("enabled state cannot be verified for RU carriers")

    def download_statistic_report(self, test_case_name: str, id: Optional[str] = None) -> None:
        """
        Description:
            download statistic report of the current run or latest run test case

        Parameter:
            test_case_name (str): The test case name
            id (str): Simnovus device id.

        Returns:
            None. This function only executes the codes and does not return any value.
        """
        UE = (
            self.testline.get_component_by_id(id)
            if id
            else self.testline.get_components_by_type("UE")[0]
        )
        # only get the test case current or the latest execution no matter test_case_name is
        if isinstance(UE, SimnovusUE):
            if Keywords.test_case_directory_path:
                log_path_directory = os.path.join(
                    Keywords.test_case_directory_path, f"UE/{UE.id}/Logs/"
                )
                UE.download_statistic_report(test_case_name, log_path_directory)
            else:
                raise FrameworkException("Test case directory does not exist!")
        else:
            raise FrameworkException("This keyword only support for Simnovus device!")

    def get_ru_state(self, ru_id: str = None) -> bool:
        """
        Description:
            This function will get the RU State.
        Parameters:
            ru_id (str): ID of the RU object to get state. Defaults is the first RU listed in the yaml file.
        Returns:
            ret_check (bool):
                True: if getting RU State successfully.
                False: if getting RU State failed.
        Raises:
            FrameworkException: If getting RU State failed at check RU TX/RX and PTP Carrier states.
        """
        ret_check = False
        if self.testline.get_components_by_classname("GenericRU"):
            if ru_id is not None:
                radio = self.testline.get_component_by_id(ru_id)
            else:
                radio = self.testline.get_components_by_classname("GenericRU")[0]
                logger.warn("No ru_id provided, will check status of first RU")
        logger.info("====== Getting RU State", also_console=True)

        # Check RU TX Carrier state.
        if radio.get_state(
            "/user-plane-configuration/tx-array-carriers/state", "READY"
        ) and radio.get_state("/user-plane-configuration/tx-array-carriers/active", "ACTIVE"):
            # Check RU RX Carrier state.
            if radio.get_state(
                "/user-plane-configuration/rx-array-carriers/state", "READY"
            ) and radio.get_state(
                "/user-plane-configuration/rx-array-carriers/active", "ACTIVE"
            ):
                logger.info(
                    "====== RU state is good (TX/RX carrier states are ready and active)\n",
                    also_console=True,
                )
                ret_check = True
            else:
                raise FrameworkException(
                    "====== RU RX Carrier state is not both READY and ACTIVE\n"
                )
        else:
            raise FrameworkException(
                "====== RU TX Carrier state is not both READY and ACTIVE\n"
            )

        return ret_check

    def trigger_alarm_with_iptables(
        self,
        component: str,
        interface: str,
        type: str,
        dest: bool = True,
        id: str = None,
    ) -> None:
        """
        Description:
            Trigger iptables command with option(with type: DROP, ACCEPT, REJECT,...) for all the packets reach to or come from components.
        Parameter:
            component (str): The components you would like to send ibtables to (i.e CUCP, CUUP and DU).
            dest (bool): Default is True.
                         True: it mean the iptables command send to component with option -d (destination).
                         to send the command with option(with type: DROP, ACCEPT, REJECT,...) for all the packets reaching to components.
                         False: it mean the iptables command send to component with option -s (source)
                         to send the command with option(with type: DROP, ACCEPT, REJECT,...) for all the packets coming from components.
            interface (str): The interface for which we need to fetch the interface ip from the TL.
            type (str): The option that iptables command use to send to component.
                        EX: DROP, ACCEPT, REJECT,...
            id (str): Component id, if none is set will do for all component of a given type. Default value is None.
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        try:
            # check the provided interface name and change to correct interface name in xml
            try:
                interface_options = {
                    "f1c": "EP_F1C",
                    "n2": "EP_NgC",
                    "e1": "EP_E1",
                }
                interface_in_xml = interface_options[interface.lower()]
            except KeyError:
                FrameworkException(
                    "This keyword currently only supports interfaces F1C, N2, E1. Please retry for these interfaces only"
                )
            if id is None:
                testline_components = self.testline.get_components_by_type(component)
                for testline_component in testline_components:
                    # fetch the interface ip from the correct interface name in xml
                    interface_ip = testline_component.fetch_interface_ip(
                        interface_in_xml
                    )
                    # check the condition to use the option -d (destination) or -s (source) for iptables command
                    if dest:
                        iptables_cmd = (
                            f"sudo iptables -A INPUT -d {interface_ip} -j {type}"
                        )
                    else:
                        iptables_cmd = (
                            f"sudo iptables -A INPUT -s {interface_ip} -j {type}"
                        )
                    testline_component.connection.sendCommand_shell(iptables_cmd)
            else:
                testline_component = self.testline.get_component_by_id(id)
                # fetch the interface ip from the correct interface name in xml
                interface_ip = testline_component.fetch_interface_ip(interface_in_xml)
                # check the condition to use the option -d (destination) or -s (source) for iptables command
                if dest:
                    iptables_cmd = f"sudo iptables -A INPUT -d {interface_ip} -j {type}"
                else:
                    iptables_cmd = f"sudo iptables -A INPUT -s {interface_ip} -j {type}"
                testline_component.connection.sendCommand_shell(iptables_cmd)
        except Exception as exc:
            raise FrameworkException(
                f"Couldn't trigger alarm with iptables command for {component} with option {type} for interface {interface}."
                f" With the error occured: {exc}"
            )

    def get_gnb_assoc_id_and_create_cli_cmd(
        self, id: str, cli_command: str, output_file: str, element_check: str
    ) -> str:
        """
        Description:
            Get gNB assoc ID for cuup/du at CUCP via 2 CLIs:
                1. echo '{"cmd": "show status", "param": ["du"]}' | evans -r -p 9089 cli call clidsrv.v1.clisrv.exec | goJson
                2. echo '{"cmd": "show status", "param": ["up"]}' | evans -r -p 9089 cli call clidsrv.v1.clisrv.exec | goJson
                3. To expand if another CLIs
            And create file to contain CLI command with Json format
        Parameter:
            id (str): the Component id given in TL yaml file to send cli command.
            cli_command: the debug cli using to get gNB assoc ID (the 1st or 2nd command above)
            output_file: Json file to contain cli cmd (provied by user)
            element_check(str): element need to get assoc ID. (du/up)
        Returns:
            gnb_assoc_id of the selected element (du/up)
        """
        cli_output = self.send_command(component_id=id, command=cli_command)
        logger.info(f"====== cli_response: {cli_output}", also_console=True)
        try:
            if cli_output is not None:
                json_content = cli_output.replace('"{', "{").replace('}"', "}")
                cli_output_dict = json.loads(json_content)
                if element_check.lower() == "du":
                    gnb_assoc_id = cli_output_dict["resp"][0]["gnb_mgr_du"][0][
                        "gnb_assoc_id"
                    ]
                else:
                    gnb_assoc_id = cli_output_dict["resp"][0]["gnb_mgr_cu_up"][0][
                        "gnb_assoc_id"
                    ]

                cmd_content = {
                    "cmd": "show status",
                    "param": ["assoc", str(gnb_assoc_id)],
                }

                # Create Json file for cli command
                with open(output_file, "w") as file:
                    json.dump(cmd_content, file)
                return str(gnb_assoc_id)
            else:
                raise Exception("Debug Cli show status Failed")
        except Exception as exc:
            raise FrameworkException(
                f"Failed to get assoc ID: {str(exc)} for component id '{id}'"
            )

    def Trigger_OAM_Config(self, xmlFilePath: str, component_id: str) -> bool:
        """
        Description:
            Trigger OAM to configure the CUCP or CUUP component through netconf-console command

        Parameter:
            component_id (str): The cucp or cuup component id which need to configure it.
            xmlFilePath (str): the configuration file full path to configure the cucp or cuup component

        Returns:
            True -> if successfully configured the cucp or cuup.
            false -> if failed to configure.

        """
        output = ""
        if "CUCP" or "CUUP" in component_id:
            component = self.testline.get_component_by_id(component_id)
            cmd = (
                f"{Global_Variables.netconf_console_path}netconf-console "
                f"--host={component.oam_ip} "
                f"--port={Global_Variables.oam_port} "
                f"--user=netconf --privKeyType=rsa --privKeyFile={Global_Variables.NETCONF_PRIVATE_KEYPATH} "
                + "--db candidate --edit-config="
                + str(xmlFilePath)
            )

            commit_cmd = (
                f"{Global_Variables.netconf_console_path}netconf-console "
                f"--host={component.oam_ip} "
                f"--port={Global_Variables.oam_port} "
                f"--user=netconf --privKeyType=rsa --privKeyFile={Global_Variables.NETCONF_PRIVATE_KEYPATH} "
                + "--commit"
            )

            logger.console("\nNetConf Command: " + cmd)
            try:
                output = component.connection.sendCommand_shell(cmd)
                commit_output = component.connection.sendCommand_shell(commit_cmd)
                if "<ok/>" in commit_output:
                    return True
                else:
                    logger.console(
                        f"\nFailed to commit config for the {component.id} through netconf-console command with output:\n{output}"
                    )
                    return False
            except Exception as e:
                logger.error("Exception while running the following command: " + str(e))
        else:
            logger.error("Recieved Unsopported Component for OAM Config")
            return False

    def Validate_Operational_State(self, id: str) -> None:
        """
        Description:
            Validate the Operational state of the gNB components.

        Parameter:
            id (str): The gNB component id which need to validate operational state.

        Returns:
            None: This function only executes the codes and does not return any value.

        """
        try:
            if id:
                testline_components = self.testline.get_component_by_id(id)
                if "Podman" in testline_components.__class__.__name__:
                    return testline_components.Validate_Operational_State()
                else:
                    logger.error(
                        f"{testline_components.__class__.__name__} not supported yet to validate Operational State"
                    )
            else:
                logger.error(
                    "Please provide the component id which you want to validate operational state"
                )
        except Exception as e:
            logger.error("Exception while running the following command: " + str(e))

    def test_line_start_skip_validation(
        self,
        num_cells: int = 1,
        config_file_name: str = None,
        components: List = None,
        check_cell_up: bool = True,
        custom_component_config: str = None,
        skip_components: list = ["CUUP1"],
    ) -> None:
        """
        Description:
            This function will start all the components of the test line. The specified first component will be started without validation & specified config file.
            The following components in the skip_components list will be brought up with default xml but no validations.

        Parameters:
            num_cells: Number of DU cells to bring up
            config_file_name (str): if modified it refers to the new config file for the component
            components (list): To start certain components base on the list id input, by default all components will be started.
            check_cell_up (bool): to know if the core components has started or not, because the DU starting message differs according to whether the 5gcore is up or not.
            skip_components (list): list of component ids to skip validation after started
            custom_component_config (str): the configuration file for specific component id

        Returns:
            None: This function only executes the codes and does not return any value.
        """
        self.component_dict = {}
        if components:
            for id in components:
                component_object = self.testline.get_component_by_id(id)
                if component_object.type in self.component_dict:
                    self.component_dict[component_object.type].append(component_object)
                else:
                    self.component_dict[component_object.type] = [component_object]
        else:
            self.component_dict = self.testline.components_dict

        current_component = ""
        components_objects = []
        self.list_components_started = components_objects
        Keywords.list_components_id_started = []
        try:
            # Create a list contains list of components objects to be passed as a paramater to "check_current_components_and_force"
            components_list = [
                value for values in self.component_dict.values() for value in values
            ]
            self.check_current_components_and_force(components_list)
            l1_exists = False
            for L1 in self.component_dict.get("L1", []):
                components_objects.append(L1)
                if L1.id not in Keywords.list_components_id_started:
                    Keywords.list_components_id_started.append(L1.id)
                current_component = "L1"
                l1_exists = True
                RU_objs = None
                if hasattr(L1, "ru_connected_id"):
                    RU_objs = []
                    for RU_Id in L1.ru_connected_id:
                        ru_object = self.testline.get_component_by_id(RU_Id)
                        RU_objs.append(ru_object)
                        # TODO added for MP-66346 revisit this after logs refactor
                        # Always consider RU objects to be started for logs collection purposes
                        if ru_object.id not in Keywords.list_components_id_started:
                            Keywords.list_components_id_started.append(ru_object.id)

                start_status = L1.start(RU_objs)
                if not start_status:
                    raise Exception("L1 start fail, exiting")

            for core in self.component_dict.get("CORE", []):
                current_component = "CORE"
                components_objects.append(core)
                if core.id not in Keywords.list_components_id_started:
                    Keywords.list_components_id_started.append(core.id)
                start_status = core.start()
                if not start_status:
                    raise Exception("CORE start fail, exiting")

            for cucp in self.component_dict.get("CUCP", []):
                current_component = "CUCP"
                components_objects.append(cucp)
                if cucp.id not in Keywords.list_components_id_started:
                    Keywords.list_components_id_started.append(cucp.id)
                if cucp.id in skip_components:
                    if custom_component_config == cucp.id:
                        cucp.config_file_name = config_file_name
                    start_status = cucp.start(skip_validation=True)
                else:
                    start_status = cucp.start()
                if not start_status:
                    raise Exception("CUCP start fail, exiting")

            for cuup in self.component_dict.get("CUUP", []):
                current_component = "CUUP"
                components_objects.append(cuup)
                if cuup.id not in Keywords.list_components_id_started:
                    Keywords.list_components_id_started.append(cuup.id)
                if cuup.id in skip_components:
                    if custom_component_config == cuup.id:
                        cuup.config_file_name = config_file_name
                    start_status = cuup.start(skip_validation=True)
                else:
                    start_status = cuup.start()
                if not start_status:
                    raise Exception("CUUP start fail, exiting")

            for du in self.component_dict.get("DU", []):
                current_component = "DU"
                components_objects.append(du)
                if du.id not in Keywords.list_components_id_started:
                    Keywords.list_components_id_started.append(du.id)
                if du.id in skip_components:
                    if custom_component_config == du.id:
                        du.config_file_name = config_file_name
                    start_status = du.start(
                        num_cells=num_cells,
                        check_cell_up=check_cell_up,
                        l1_exists=l1_exists,
                        skip_validation=True,
                    )
                else:
                    start_status = du.start(
                        num_cells=num_cells,
                        check_cell_up=check_cell_up,
                        l1_exists=l1_exists,
                    )
                if not start_status:
                    raise Exception("DU start fail, exiting")
            for radio in self.component_dict.get("RU", []):
                timeout = radio.timeout
                if hasattr(radio, "port_check"):
                    if self.get_ru_state(radio.id) is False:
                        raise FrameworkException("RU state is not good")
                else:
                    logger.info("Wait for RU state is good", also_console=True)
                    time.sleep(timeout)

            for ue in self.component_dict.get("UE", []):
                current_component = "UE"
                components_objects.append(ue)
                Keywords.list_components_id_started.append(
                    ue.id[0] if isinstance(ue.id, list) else ue.id
                )
                start_status = ue.start()
                if not start_status:
                    raise Exception("UE start fail, exiting")

        except Exception as e:
            BuiltIn().set_suite_variable("${SKIP_TEST}", "True")
            # collect logs when failed in test line start
            log_directory = Keywords.test_suite_directory_path
            component_objects = Keywords.get_list_started_components()
            self.log_manager.transfer_logs(component_objects, log_directory, copy_coredump="True")
            raise FrameworkException(
                f"====== Test Line start failed in {current_component} due to : {str(e)}"
            ) from e

    def traffic_profile_load(
        self, profile_name: str, ids: Optional[List[str]] = None
    ) -> ptr.BaseProfile:
        """
        Description: Looks for a profile matching the profile name in the generic profile and vendor listings.
        Parameters:
            profile_name (str): The name of the profile to look for
            ids (List[str]): The ids of the UEs to run the profile on.

        Returns:
            A base profile (either generic or vendor specific)
        Unit Test: framework/unit_tests/keywords/traffic_profile_unit_test.py
        """
        generic_path = f"./resources/traffic_profiles/{profile_name}.json"
        # Returns true if the UE type is in the tuple of classes that support generic profiles
        ue_ids = []
        if ids:
            UEs = []
            for id in ids:
                UEs.append(self.testline.get_component_by_id(id))
            ue_ids = ids
        else:
            UEs = self.testline.get_components_by_type("UE")
            for ue in UEs:
                ue_ids.append(ue.id)
        ue_type = type(UEs[0])
        logger.info(
            f"Looking for traffic profile: {profile_name} on UEs with type {ue_type}",
            also_console=True,
        )
        if os.path.exists(generic_path):
            generic_profile = ptr.GenericTrafficProfile.from_json(generic_path)
            logger.info(
                f"Generic Traffic Profile is loaded with info: {pprint.pformat(generic_profile.__dict__)}",
                also_console=True
            )
            if ue_type is AndroidUE:
                logger.info(
                    f"Android Traffic Profile is loaded with info: {pprint.pformat(ptr.AndroidTrafficProfile.from_generic(generic_profile, ue_ids).__dict__)}",
                    also_console=True
                )
                return ptr.AndroidTrafficProfile.from_generic(generic_profile, ue_ids)
            return generic_profile

        elif isinstance(UEs[0], SimnovusUE) and UEs[0].test_case_exists(profile_name):
            logger.info(
                f"Simnovous Traffic Profile is loaded with info: {pprint.pformat(ptr.SimnovusTrafficProfileReference(profile_name).__dict__)}",
                also_console=True
            )
            return ptr.SimnovusTrafficProfileReference(profile_name)
        elif isinstance(
            UEs[0], SimnovusUE
        ):  # TODO This line cover the MP-61191 and will be automatically correct with 2 condition lines before
            profile = ptr.SimnovusTrafficProfileReference(profile_name)
            profile.name = BuiltIn().get_variable_value("$TEST_NAME")
            profile.is_modifiable: bool = True
            logger.info(
                f"Simnovus Traffic Profile is loaded with info: {pprint.pformat(profile.__dict__)}",
                also_console=True
            )
            return profile
        elif isinstance(UEs[0], TM500UE):
            logger.info(
                f"TM500 Traffic Profile is loaded with info: {pprint.format(ptr.TM500TrafficProfileReference(profile_name).__dict__)}",
                also_console=True
            )
            return ptr.TM500TrafficProfileReference(profile_name)
        raise FileNotFoundError(
            f"There are no generic profiles or vendor profiles matching {profile_name}."
        )

    @staticmethod
    def traffic_profile_set(profile: ptr.BaseProfile, field: str, value: Any) -> None:
        """
        Description: Modifies the provided fields of the profile.
        Parameters:
            profile: The profile whose fields will be modified.
            field: The field name to be modified.
            value: The value to associate with the field being modified.
        Returns: None
        """
        logger.info("Setting Traffic Profile", also_console=True, banner=True)
        if not profile.is_modifiable:
            raise FrameworkException(f"Profile {profile.name} is not modifiable")

        """
        Field_indexes will include list of keys which are path to our target field
        For example, if we want to change signalling_pattern.sig_pattern1.UE_Connected_Time field
        field_indexes will be ['name', 'signalling_pattern', 'traffic_pattern', 'subscriber_group']
        """
        field_indexes = field.split(".")
        section = field_indexes.pop(0)
        if len(field_indexes) == 0:
            setattr(profile, field, value)
        elif len(field_indexes) == 1:
            field = field_indexes.pop(-1)
            profile.section[field] = value
        else:
            profile_section = {}
            field = field_indexes.pop(-1)
            if section == 'signalling_pattern':
                profile_section = profile.signalling_pattern
            elif section == 'traffic_pattern':
                profile_section = profile.traffic_pattern
            elif section == 'subscriber_group':
                profile_section = profile.subscriber_group

            for index in field_indexes:
                profile_section = profile_section[index]
            profile_section[field] = value

    def traffic_profile_run(
        self,
        profile: ptr.BaseProfile,
        ids: Optional[List[str]] = None,
        num_cells: Optional[int] = None,
    ) -> None:
        """
        Description: Runs the provided traffic profile.
        Parameters:
            profile (ptr.BaseProfile): The traffic profile to be run.
            ids (List[str]): The ids of the UEs to run the profile on.
            num_cells (int): Number of cells to scale out profile to, else use number in profile

        Returns: None.
        Unit Test: framework/unit_tests/keywords/traffic_profile_unit_test.py
        """
        logger.info("Running Traffic Profile", also_console=True, banner=True)

        if ids:
            UEs = []
            for id in ids:
                UEs.append(self.testline.get_component_by_id(id))
        else:
            UEs = self.testline.get_components_by_type("UE")

        same_class = all(isinstance(UE, type(UEs[0])) for UE in UEs)
        if not same_class:
            raise NotImplementedError("Cannot run traffic profile on UEs of different types")
        ue_type = type(UEs[0])

        # TODO: Figure out DU and UE mapping. For now, choosing the first available DU in the TL inventory yaml file
        DU = self.testline.get_components_by_type("DU")[0]
        try:
            # Get the numberOfRBs from downlink BWP section of DU config file
            DU.no_of_rbs = utils.get_config_value_through_netconf(
                connection=DU.connection,
                netconf_cmd=f"{Global_Variables.netconf_console_path}/netconf-console --host={DU.oam_ip} --port={Global_Variables.oam_port}  --user=netconf --privKeyType=rsa --privKeyFile={Global_Variables.NETCONF_PRIVATE_KEYPATH}",
                xpath="/ManagedElement/GNBDUFunction/BWP[1]/attributes",
                element="numberOfRBs"
            )
        except paramiko.SSHException:
            logger.warn("Resetting ssh connection")
            DU.connection.reset()
            DU.no_of_rbs = utils.get_config_value_through_netconf(
                connection=DU.connection,
                netconf_cmd=f"{Global_Variables.netconf_console_path}/netconf-console --host={DU.oam_ip} --port={Global_Variables.oam_port}  --user=netconf --privKeyType=rsa --privKeyFile={Global_Variables.NETCONF_PRIVATE_KEYPATH}",
                xpath="/ManagedElement/GNBDUFunction/BWP[1]/attributes",
                element="numberOfRBs"
            )
        except TypeError as te:
            logger.error(f"{te}")
            raise te
        except Exception as exc:
            raise exc
        logger.info(
            f"Running traffic profile: {pprint.pformat(profile.__dict__)}",
            also_console=True,
        )

        # Convert generic profiles into specific ones first
        if isinstance(profile, ptr.GenericTrafficProfile):
            if num_cells is not None:
                profile.add_cells(num_cells)
            if ue_type is SimnovusUE:
                UE = UEs[0]
                profile = ptr.SimnovusTrafficProfile.from_generic(profile, UE, DU)
                logger.info(
                    f"Running Simnovus traffic profile converted from a generic profile: {pprint.pformat(profile.__dict__)}",
                    also_console=True
                )
                logger.info(
                    f"JSON payload to send to Simnovus: {json.dumps(profile.data)}"
                )
                UE.upload_or_modify_test(profile.name, profile.data)
                UE.start_test_case(profile.name)
                return
            elif ue_type is AndroidUE:
                logger.info(
                    f"Running Android traffic profile: {pprint.pformat(profile.__dict__)}",
                    also_console=True
                )
                profile.update_traffic_info()
                self.signaling_threads = []
                self.android_profile_thread_instance.start_thread_logging()
                self.signaling_thread = threading.Thread(
                    target=utils.safe_thread_execution, args=(profile.signal_android_ue, UEs, self.traffic_manager), name=UEs[0].id
                )
                self.signaling_thread.start()
                self.signaling_threads.append(self.signaling_thread)
            else:
                raise NotImplementedError(
                    f"Profile translation is not supported for UE of type {type(UE)}"
                )

        # At this point, all profiles are specific or references
        if ue_type is SimnovusUE:
            UE = UEs[0]
            if isinstance(profile, ptr.SimnovusTrafficProfileReference):
                UE.start_test_case(profile.name)
                return
            elif isinstance(profile, ptr.SimnovusTrafficProfile):
                UE.upload_or_modify_test(profile.name, profile.data)
                UE.start_test_case(profile.name)
                return
            else:
                raise ValueError(
                    f"Profile of type {type(profile)} cannot be translated for UE of type {type(UE)}"
                )
        elif ue_type is AndroidUE:
            core = self.testline.get_components_by_type("CORE")
            if isinstance(core, list) and len(core) > 0:
                core = core[0]
            if len(UEs) > 1:
                logger.error("Currently, we only support single UE for running Android traffic profile!")
            else:
                try:
                    UE = UEs[0]
                    if isinstance(profile, ptr.AndroidTrafficProfile):
                        while not (UE.state == State.Attached.value):
                            if profile._stop_event.is_set():
                                raise Exception(f"An error occurred during signalling Android UE {UE.id}!")
                        UE.run_traffic_profile(profile, core)
                    else:
                        raise ValueError(
                            f"Profile of type {type(profile)} cannot be translated for UE of type {type(UE)}"
                        )
                except Exception as e:
                    profile.stop_signaling_thread()
                    for thread in self.signaling_threads:
                        thread.join()
                    self.android_profile_thread_instance.stop_thread_logging(self.signaling_threads)
                    raise e
        else:
            raise NotImplementedError(
                f"UE of type {ue_type} cannot run traffic profiles yet."
            )

    def traffic_profile_stop(
        self,
        profile: ptr.BaseProfile,
        ids: Optional[List[str]] = None,
    ) -> None:
        """
        Description: Stop traffic profile is completed.
        Parameters:
            profile (ptr.BaseProfile): The traffic profile to be run.
            ids (List[str]): The ids of the UEs to run the profile on.
        Returns: None.
        Unit Test: framework/unit_tests/keywords/traffic_profile_unit_test.py
        """
        if ids:
            UEs = []
            for id in ids:
                UEs.append(self.testline.get_component_by_id(id))
        else:
            UEs = self.testline.get_components_by_type("UE")
        same_class = all(isinstance(UE, type(UEs[0])) for UE in UEs)
        if not same_class:
            raise NotImplementedError("Cannot stop traffic profile on UEs of different types")
        ue_type = type(UEs[0])

        # At this point, all profiles are specific or references
        if ue_type is SimnovusUE:
            UE = UEs[0]
            logger.info(
                f"Stop traffic profile: {profile} on Simnovus device id {UE.id}",
                also_console=True,
            )
            if isinstance(profile, ptr.GenericTrafficProfile) or isinstance(profile, ptr.SimnovusTrafficProfileReference):
                UE.stop_test_case(profile.name)
                return
            else:
                raise ValueError(
                    f"Profile of type {type(profile)} is not Generic Traffic Profile or "
                    f"Traffic Profile Reference for UE of type {type(UE)}"
                )
        elif ue_type is AndroidUE:
            core = self.testline.get_components_by_type("CORE")
            if isinstance(core, list) and len(core) > 0:
                core = core[0]
            profile.stop_signaling_thread()
            for thread in self.signaling_threads:
                thread.join()
            self.android_profile_thread_instance.stop_thread_logging(self.signaling_threads)
            for UE in UEs:
                UE.set_can_attach(True)
        else:
            raise FrameworkException(
                f"UE of type {ue_type}: Fail to stop for test case."
            )

    def check_for_new_PM_file_generated(
        self, component_ids: list[str], job_id: int = 0
    ) -> dict:
        """
        Description:
            Waits for a new PM file to be generated and then returns the latest file name for the component_ids

        Parameters:
            component_ids (list): The list of the component_id name. Default = CUCP, CUUP, DU
            job_id (int): The PM job id that this function should filter for. Default = 0

        Returns:
            dict: The latest filename for that component_id. Example: {CUCP: latest_cucp_pm_filename}
        """
        if not component_ids:
            raise FrameworkException(
                "No component ID has been provided to poll for PM file, please provide "
                "component ID as input"
            )

        tmp_last_pm_file = (
            {}
        )  # Stores the current latest PM file name for the component_id
        latest_pm_files = (
            {}
        )  # Stores the latest PM file name for the component_id (the next file that's generated after the above)
        report_interval = (
            {}
        )  # Stores the reporting interval of every component_id to raise exception if polling for longer than configured time

        # Retrieve the configured reporting interval for the component_id
        for component_id in component_ids:
            try:
                component = self.testline.get_component_by_id(component_id)
                report_interval[component_id] = component.fetch_reporting_period(job_id)
            except Exception as err:
                raise FrameworkException(
                    f"Failed to retrieve reporting period for: {component_id} "
                    f"because object is not instantiated in TLO: {err}"
                )

        # Loop until all the component_ids get their latest PM file
        start_time = time.time()
        while len(latest_pm_files) != len(component_ids):
            for component_id in component_ids:
                if component_id in latest_pm_files:
                    continue

                # Raise exception if couldn't find PM file after trying for the confiugred amount of time (+60 seconds)
                if time.time() - start_time > report_interval[component_id] * 60 + 60:
                    raise ComponentPMFailure(
                        f"Failed to retrieve latest PM file for component: {component_id} after trying for the configured amount of time for reporting interval ({report_interval[component_id]} min)"
                    )

                component = self.testline.get_component_by_id(component_id)
                file_name = []
                if DeploymentEnv.PODMAN is component.get_deployment_env():
                    # TODO: Workaround for DU until MP-88080 is resolved. After resolution remove if and keep only code in else
                    if component.type == "DU":
                        oama_components = self.testline.check_components_by_type_exist("OAMA")
                        if oama_components:
                            podman_container_name = oama_components[0].podman_container_name
                            shell_cmd = f"ls -t {oama_components[0].container_bin_path} | grep .*job{job_id}.*xml | head -1"
                        else:
                            raise FrameworkException("Cannot locate PM files because OAM does not exist on test line. PM files are stored in OAMA container")
                    else:
                        podman_container_name = component.podman_container_name
                        shell_cmd = f"ls -t {component.pm_report_directory} | grep .*job{job_id}.*xml | head -1"
                    file_name = component.connection.send_command_and_extract_output(
                        f"podman exec {podman_container_name} bash -c '{shell_cmd}'"
                    )
                else:
                    shell_cmd = f"ls -t {component.pm_report_directory} | grep .*job{job_id}.*xml | head -1"
                    file_name = component.connection.send_command_and_extract_output(
                        f"{shell_cmd}"
                    )

                # Check if the command has any output
                if file_name:
                    file_name = file_name[0]
                else:
                    file_name = ""

                if component_id not in tmp_last_pm_file:
                    tmp_last_pm_file[component_id] = file_name
                else:
                    if file_name != tmp_last_pm_file[component_id]:
                        latest_pm_files[component_id] = file_name
        return latest_pm_files

    def get_current_alarm_time(self) -> None:
        """
        Description:
            To get current alarm timestamp with UTC timezone
            To get current component server timestamp

        Parameters: None

        Returns:
            Current UTC time zone
        """
        self.alarm_start_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")
        self.server_start_time = self.get_component_current_time(component_id="CUCP1", format="%Y/%m/%d %H:%M:%S")

    def generate_ran_test_report(self) -> None:
        """
        Description:
            Function to generate test report.

        Parameters: None

        Returns: None
        """
        try:
            logger.info("Start generate ran test report...", also_console=True)
            report = ReportData(self.testline)
            report.generate_ran_test_report(
                self.TL_name, self.alarm_start_time, self.server_start_time
            )
        except Exception as e:
            raise FrameworkException(f"Generate ran test report failed due to {e}")

    def get_data_from_UE_log(self, ue_type: str, data: str , id: str = None) -> None:
        """
        Description:
            Get the wanted data from the ue csv stat log
        Parameters:
            ue_type (str): simnovus, realUE, TM500 (currently support simnovus only)
            data (str): There are 2 input cases with different result:
                        input "all" or don't input(None): to get all pre-defined default data in the csv file
                        string contains specified columns (Ex: RSRP RSRQ): to getting specified stat columns and only the input columns would be gotten
            id (str): Simnovus device id
        Return:
            ue_data.csv file
        """
        UE = (
            self.testline.get_component_by_id(id)
            if id
            else self.testline.get_components_by_type("UE")[0]
        )
        # Get the path to the local csv uestat file and its name
        log_path_directory = (
            os.path.join(Keywords.test_case_directory_path, f"UE/{UE.id[0]}/Logs/")
            if isinstance(UE.id, list)
            else os.path.join(Keywords.test_case_directory_path, f"UE/{UE.id}/Logs/")
        )
        source_file_path = UE.get_uestat_source_file_path(log_path_directory)
        if not source_file_path:
            raise FrameworkException(f"Could not find any csv stat log under {log_path_directory}")
        origin_file_name = source_file_path.split("\\")[-1]
        # Check if the column stat will get at default or input only
        if data.lower() == "all":
            if ue_type.lower() == "simnovusue":
                UE.get_specified_UE_stats_log(source_file_path, origin_file_name)
            elif ue_type.lower() == "tm500":
                pass
            elif ue_type.lower() == "realue":
                pass
            else:
                raise FrameworkException(
                    "the ue type you input is not supported at the moment"
                )
        else:
            if ue_type.lower() == "simnovusue":
                UE.get_specified_UE_stats_log(source_file_path, origin_file_name, data)
            elif ue_type.lower() == "tm500":
                pass
            elif ue_type.lower() == "realue":
                pass
            else:
                raise FrameworkException(
                    "the ue type you input is not supported at the moment"
                )

    def clean_up_confd_data_base(self, component_ids: List[str] = None) -> None:
        """
        Description:
            This function will clean up the confd data base for gNB components.
        Parameters:
            component_ids (list[str]): components list will be cleaned up the confd data base.
                E.g. components = ["CUCP1","CUUP1","DU1"]
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        for component_id in component_ids:
            logger.info(
                f"\nCleaning up the netconf data base for {component_id} component..\n",
                also_console=True,
            )
            component_object = self.testline.get_component_by_id(component_id)
            # Calling clean_up_confd_data_base function from utils.py to clean up the confd data base for component.
            utils.clean_up_confd_data_base(component_object)

    def start_acm(self, id: str = None) -> None:
        """
        Description:
            Starts the ACM Service.

        Parameters:
            id(str): The id of DU object to start ACM (Eg. DU1). Otherwise, start ACM on all DU objects in yaml.

        Returns:
            None: This function only executes the codes and does not return any value.
        """

        # The code module below starts the ACM service
        if id is not None:
            du_object = self.testline.get_component_by_id(id)
            acm_start_status = du_object.start_acm()
            if acm_start_status:
                logger.info(
                    f"====== ACM service of '{du_object.id}' is started successfully\n",
                    also_console=True,
                )
            else:
                raise FrameworkException(
                    f"ACM service of '{du_object.id}' was not started successfully"
                )
        else:
            list_du_objects = self.testline.get_components_by_type("DU")
            for du_object in list_du_objects:
                acm_start_status = du_object.start_acm()
                if acm_start_status:
                    logger.info(
                        f"====== ACM service of '{du_object.id}' is started successfully\n",
                        also_console=True,
                    )
                else:
                    raise FrameworkException(
                        f"ACM service of '{du_object.id}' was not started successfully, "
                    )

    def stop_acm(self, id: str = None) -> None:
        """
        Description:
            Stops the ACM Service.

        Parameters:
            id(str): The id of DU object to stop ACM (Eg. DU1). Otherwise, stop ACM on all DU objects in yaml.

        Returns:
            None: This function only executes the codes and does not return any value.
        """
        if id is not None:
            du_object = self.testline.get_component_by_id(id)
            acm_stop_status = du_object.stop_acm()
            if acm_stop_status:
                logger.info(
                    f"====== ACM service of '{du_object.id}' is stopped successfully\n",
                    also_console=True,
                )
            else:
                raise FrameworkException(
                    f"ACM service of '{du_object.id}' is not stopped successfully, exiting"
                )
        else:
            list_acm_stop_failed = []
            list_du_objects = self.testline.get_components_by_type("DU")
            for du_object in list_du_objects:
                try:
                    acm_stop_status = du_object.stop_acm()
                    if acm_stop_status:
                        logger.info(
                            f"====== ACM service of '{du_object.id}' is stopped successfully\n",
                            also_console=True,
                        )
                    else:
                        list_acm_stop_failed.append(du_object.id)
                except Exception:
                    list_acm_stop_failed.append(du_object.id)
                    continue
            if list_acm_stop_failed:
                raise FrameworkException(
                    f"Failed to stop ACM service of DU component(s): {list_acm_stop_failed}"
                )

    def get_acm_status(self, id: str = None) -> None:
        """
        Description:
            Get the ACM service status and display the status to console

        Parameters:
            id: The id of DU object to Check the ACM service status (Eg. DU1). Otherwise, check ACM service status on all DU objects in yaml

        Returns:
            None: This function only executes the codes and does not return any value.
        """
        if id is None:
            logger.info(
                "====== No DU id provided. Will check ACM service status on all DU components\n",
                also_console=True,
            )
            du_object = self.testline.get_components_by_type("DU")
            for DU in du_object:
                self.get_acm_status(DU.id)
            return
        logger.info(
            f"====== Checking ACM service status on {id}\n",
            also_console=True,
        )
        du_object = self.testline.get_component_by_id(id)
        acm_status = du_object.get_acm_status()
        if acm_status is True:
            logger.info(
                f"====== ACM service status on {du_object.id} is active and running",
                also_console=True,
            )
        else:
            logger.warn(
                f"====== ACM service status on {du_object.id} is inactive and not running"
            )

    def get_component_current_time(self, component_id: str, format: str = None) -> str:
        """
        Description:
            This method will return current datetime for a specific component

        Parameters:
            component_id (str): The id of the component that's defined in the YAML file (ie: CUCP1)
            format (str): The timestamp format. Default is None.

        Return:
            current_time (str): The current datetime as a string for that component
        """
        component = self.testline.get_component_by_id(component_id)
        if DeploymentEnv.PODMAN is component.get_deployment_env():
            date_cmd = f'TZ="GMT" date +"{format}"' if format else 'TZ="GMT" date'
        else:
            date_cmd = f'date +"{format}"' if format else "date"
        current_time = component.connection.sendCommand(date_cmd).strip()
        return current_time

    def bring_down_rusim_carrier_active_daemon(
        self, ru_sim_id: str, component_id: str = None
    ) -> None:
        """
        Description:
            This function will kill carrier active daemon in the Rusim and verify it.
        Parameters:
            ru_sim_ids(list): The list of RU Sim ids. Ex: ru_sim_ids=["ru_sim_1", "ru_sim_2", "ru_sim_3", "ru_sim_4", "ru_sim_5"]
                                       If ru_sim_id is None, then default will get ru_sim_instance_id=["ru_sim_1"] in yaml file.
                        component_id(str): component id. If id is None, then default will start first DU component.
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        if component_id is not None:
            du_object = self.testline.get_component_by_id(component_id)
        else:
            du_object = self.testline.get_components_by_type("DU")[0]
        my_str = "r\\s" + str(ru_sim_id)
        bring_down_command = (
            f"kill -9 $(ps -afe | grep carrier_active_daemon | "
            f"grep '{my_str}' | "
            r"awk '{print $2}')"
        )
        command = f"ps -afe | grep carrier_active_daemon | grep '{my_str}'"
        du_object.connection.sendCommand_shell(bring_down_command)
        output = du_object.connection.sendCommand_shell(command)
        logger.info(output)
        if "notifier/carrier_active_daemon" not in output:
            logger.info(
                "Rusim "
                + str(ru_sim_id)
                + " carrier_active_daemon successfully killed!\n",
                also_console=True,
            )
        else:
            logger.info("Rusim " + str(ru_sim_id) + " carrier_active_daemon could not get killed. Check for errors!\n", also_console=True)

    def reboot_ru_via_pdu_remote(self, ru_ids: List[str] = None) -> None:
        """
        Description:
            This function will reboot RUs via PDU Remote.
        Parameters:
            ru_ids (List[str]): list of RU ids will be rebooted. If None is set will reboot all RUs in yaml file.
                E.g. ru_ids = ["RU1","RU2"]
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        if ru_ids is not None:
            ru_objects = []
            for ru_id in ru_ids:
                ru_objects.append(self.testline.get_component_by_id(ru_id))
        else:
            logger.info(
                "\nNo ru_ids provided, will reboot all RUs in yaml file!", also_console=True
            )
            ru_objects = self.testline.get_components_by_classname("GenericRU")
        for ru_object in ru_objects:
            if not hasattr(ru_object, "pdu_remote_management_ip") or not hasattr(ru_object, "pdu_outlet_name"):
                logger.warn(
                    f"====== pdu_remote_management_ip or pdu_outlet_name of {ru_object.id} "
                    "has not been implemented in yaml file."
                )
                logger.warn(
                    "====== RU will not be rebooted. ======"
                )
            else:
                logger.info(
                    f"====== Starting to reboot {ru_object.id} via PDU remote...", also_console=True
                )
                remote_pdu = RemotePduSnmp(ru_object.pdu_type_name)
                remote_pdu.remote_pdu_outlet_state(
                    host=ru_object.pdu_remote_management_ip,
                    target_state="immediateOff",
                    outlet_name=ru_object.pdu_outlet_name,
                )
                remote_pdu.remote_pdu_outlet_state(
                    host=ru_object.pdu_remote_management_ip,
                    target_state="immediateOn",
                    outlet_name=ru_object.pdu_outlet_name,
                )
                logger.info(
                    f"====== Reboot {ru_object.id} via PDU remote successfully!", also_console=True
                )

    def get_testline_component_info(
        self, component_id: str
    ):
        """
        Description:
            This function will return a component given its id.
        Parameters:
            component_id(str): component id. If id doesn't match a component or matches multiple raises exception.
        Returns:
            component : Returns the component object matching the id given.
        """
        return self.testline.get_component_by_id(component_id)

    def modify_config_json_file(self, yaml_template: str) -> None:
        """
        Description:
            This function will modify the JSON configuration file for the component.
        Parameters:
            yaml_template (str): The YAML file contains the custom configuration.
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        try:
            logger.info(f"====== Start modify config json with yaml_template: {yaml_template}", also_console=True, banner=True)

            custom_yaml_dict = utils.read_yaml_file(yaml_template)
            for component_id in custom_yaml_dict:
                component_object = self.testline.get_component_by_id(component_id)
                ConfigModification().modify_config_json_file(
                    component_object, custom_yaml_dict[component_id]
                )
        except Exception as e:
            raise FrameworkException(
                    f"The keyword modify config json file failed due to: {e}"
                )

    def revert_config_json_file(self, yaml_template: str) -> None:
        """
        Description:
            This function will revert the JSON configuration file to default for the component.
        Parameters:
            yaml_template (str): The YAML file contains the custom configuration.
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        try:
            logger.info(f"====== Start revert modified config json with yaml_template: {yaml_template}", also_console=True, banner=True)

            custom_yaml_dict = utils.read_yaml_file(yaml_template)
            for component_id in custom_yaml_dict:
                component_object = self.testline.get_component_by_id(component_id)
                ConfigModification().revert_config_json_file(
                        component_object, custom_yaml_dict[component_id]
                    )
        except Exception as e:
            raise FrameworkException(
                    f"The keyword revert modified config json file failed due to: {e}"
                )

    def deactivate_l1_gnss(self, component_id):
        """
        Description:
            This function will push the netconf config that disables the Gnss on the component.
        Parameters:
            component_id(String): The id of the component
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        logger.info("====== Disable Gnss input Via SW", also_console=True)
        self.configure_component(
            "DU", config_file="resources/netconf/deactivate_Gnss_Cell.xml", id=component_id
        )

    def activate_l1_gnss(self, component_id):
        """
        Description:
            This function will push the netconf config that enables the Gnss on the component.
        Parameters:
            component_id(String): The id of the component
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        logger.info("====== Enable Gnss input Via SW", also_console=True)
        self.configure_component(
            "DU", config_file="resources/netconf/activate_Gnss_Cell.xml", id=component_id
        )

    def add_extra_param(self, component_id: str, extra_param: str):
        """
        Description:
            This function will add an extra parameter to the start command of the component.
        Parameters:
            component_id (str): The id of the component
            extra_param (str): The extra parameter
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        try:
            logger.info(
                f"====== Adding extra param: {extra_param} into run command of component: {component_id}\n",
                also_console=True
            )
            component = self.testline.get_component_by_id(component_id)
            if hasattr(component, "extra_param"):
                if component.extra_param:
                    component.extra_param = f"{component.extra_param} {extra_param}"
                else:
                    component.extra_param = extra_param
            else:
                raise FrameworkException(
                    f"Component {component_id} does NOT support to add extra param"
                )
        except Exception as e:
            raise FrameworkException(
                f"Failed to add extra param for component {component_id} due to: {e}"
            )

    def restore_default_tl_config(self, components_ids: List = None):
        """
        Description:
            Restore the default Test Line configuration after a custom configuration in the test case.

        Parameters:
            components_ids (list): To restore certain components, by default all components will be restored.

        Returns:
            None: This function only executes the codes and does not return any value.
        """
        logger.info("Restoring the default Test Line configuration", also_console=True, banner=True)
        try:
            components = (
                [self.testline.get_component_by_id(id) for id in components_ids]
                if components_ids
                else self.testline.components)
            # reset the modified_config_file and extra_param variable to None
            for component in components:
                if hasattr(component, "modified_config_file"):
                    component.modified_config_file = None
                if hasattr(component, "extra_param"):
                    component.extra_param = None
            logger.info(
                "Restart components to recovery the setup with default TL configuration!",
                also_console=True,
            )
            self.restart_components(components_ids)
        except Exception as e:
            logger.error(
                "Exception: Failed to Restore the default Test Line configuration with error:"
                + str(e)
                + " occurred."
            )

    def switch_access_point(self, apn: str = 'internetAM', id: Optional[str] = None):
        """
        Description:
            Switching access point on Real UE.
            Using this KW at teardown phase with no apn input to revert to default setting (internetAM)

        Parameters:
            apn (str): Access point name want to switch to (create)
                    internetAM: RLC_AM - TCP & UDP (default)
                    internetUM: RLC_UM - UDP only
            id (str): Real UE id

        Returns:
            None: This function only executes the codes and does not return any value.
        """
        logger.info(f"Switching access point to {apn}", also_console=True, banner=True)
        try:
            supported_apns = ['internetAM', 'internetUM']
            UE = (
                self.testline.get_component_by_id(id)
                if id
                else self.testline.get_components_by_type("UE")[0]
            )
            if UE.__class__.__name__ == "AndroidUE":
                if apn in supported_apns:
                    UE.switch_access_point(apn)
                    logger.info(f"Switching to {apn} successfully.")
                else:
                    raise FrameworkException(f"Currently support for {supported_apns} only, but got {apn}!")
            else:
                raise FrameworkException("This keyword only support for Android UE!")
        except Exception as e:
            raise FrameworkException(
                    f"Issue occurs during execution. Due to: {e}"
                )

    def get_gnb_version(self, components_ids: List = None):
        """
        Description:
            To get the gNodeB Version and publish gNodeB build information by default in console and log.html

        Parameters:
            components_ids(list): To get certain components, by default is all gNodeB components will get the version.

        Returns:
            None: This function only executes the codes and does not return any value.
        """
        try:
            if components_ids:
                for component in components_ids:
                    if isinstance(component, list):
                        components_ids.extend(component)
                        components_ids.remove(component)
            components = (
                [self.testline.get_component_by_id(id) for id in components_ids]
                if components_ids
                else self.testline.components)
            for component in components:
                if hasattr(component, "get_version"):
                    version = component.get_version()
                    if isinstance(version, dict):
                        for version_key, version_value in version.items():
                            if version_value != "N/A":
                                version_number = re.search(r'\d+\.\d+\.\d+\.\d+-\d+', version_value)
                                if version_number:
                                    logger.info(f"{component.id} {version_key} version is: {version_number.group()}", also_console=True, banner=True)
                    elif component.type == "RU" and "GenericRU" in type(component).__name__:
                        logger.info(f"{component.id} version is: {version}", also_console=True, banner=True)
                    else:
                        if version != "N/A":
                            version_number = re.search(r'\d+\.\d+\.\d+\.\d+-\d+', version)
                            if version_number:
                                logger.info(f"{component.type if isinstance(component.id, list) else component.id} version is: {version_number.group()}", also_console=True, banner=True)
        except Exception as e:
            logger.error(
                f"Exception: Failed to get gNBs Version for {component.id} with error:"
                + str(e)
                + " occurred."
            )

    def apply_rpc_through_netconf_console(
        self,
        component: str,
        rpc_payload: str = "",
        rpc_payload_file: str = "",
        rpc_template_file: str = "",
        expected_string: str = "<ok/>",
        id: str = None,
        skip_payload_check: bool = False
    ) -> None:
        """
        Description:
            Apply RPC through netconf console for components.

        Parameters:
            component (str): The component name. E.g. CORE, CUUP, CUCP, DU, UE, MinervaL1, RU.
            rpc_payload (str, Optional): The RPC payload to be applied. default '' will check the rpc_payload_file and read its content.
            rpc_payload_file (str, Optional): The RPC payload file to be applied. default ''.
            rpc_template_file (str, Optional): The RPC template file to be applied. default ''. Supports for gNB components.
            expected_string (str, Optional): The expected string after applying the RPC. default '<ok/>'.
            id (str, Optional): The id of the component. default None so check all components with same type.
            skip_payload_check (bool, Optional): Skip the rpc payload check. default False.

        Returns:
            None: This function only executes the codes and does not return any value.
        """
        logger.info(f"Configuring Component: '{component}' through applying rpc payload", also_console=True, banner=True)
        try:
            if rpc_payload_file != "":
                with open(rpc_payload_file, "r") as f:
                    rpc_payload = f.read()
        except Exception as e:
            raise FrameworkException(
                f"Failed to open rpc payload file for Component: '{component}' due to: {e}"
            )
        # Components in testline object:
        try:
            if component in ["CORE", "CUUP", "CUCP", "DU", "UE", "MinervaL1", "RU"]:
                if id is None:
                    testline_components = self.testline.get_components_by_type(
                        component
                    )
                    for testline_component in testline_components:
                        if rpc_template_file != "":
                            rpc_payload_file = ConfigModification().generate_rpc_payload_file_from_rpc_template(
                                component_object=testline_component,
                                rpc_template_file=rpc_template_file
                            )
                            with open(rpc_payload_file, "r") as f:
                                rpc_payload = f.read()
                        config_status = utils.apply_rpc_through_netconf_console(connection=testline_component.connection,
                                                                                oam_ip=testline_component.oam_ip,
                                                                                netconf_console_path=Global_Variables.netconf_console_path,
                                                                                oam_port=Global_Variables.oam_port,
                                                                                rpc_payload=rpc_payload,
                                                                                expected_string=expected_string,
                                                                                skip_payload_check=skip_payload_check)
                        if not config_status:
                            logger.error(f"Failed to apply RPC through netconf console for {component} with id {testline_component.id}")
                else:
                    testline_component = self.testline.get_component_by_id(id)
                    if rpc_template_file != "":
                        rpc_payload_file = ConfigModification().generate_rpc_payload_file_from_rpc_template(
                            component_object=testline_component,
                            rpc_template_file=rpc_template_file
                        )
                        with open(rpc_payload_file, "r") as f:
                            rpc_payload = f.read()
                    config_status = utils.apply_rpc_through_netconf_console(connection=testline_component.connection,
                                                                            oam_ip=testline_component.oam_ip,
                                                                            netconf_console_path=Global_Variables.netconf_console_path,
                                                                            oam_port=Global_Variables.oam_port,
                                                                            rpc_payload=rpc_payload,
                                                                            expected_string=expected_string,
                                                                            skip_payload_check=skip_payload_check)
                    if not config_status:
                        logger.error(f"Failed to apply RPC through netconf console for {component} with id {testline_component.id}")
            else:
                raise Exception(f"{component} does not support configure function")
        except Exception as e:
            raise FrameworkException(f"Failed to configure {component} due to: {e}")

    def get_config(
        self, component: str, xpath: str, expected_check: str = None, id: str = None, is_xpath: bool = True
    ) -> list:
        """
        Description:
            This function is used to get Netconf Configuration and returns a list of values collected via netconf.
        Parameters:
            component (str): component will check configure. Component[CUCP, CUUP, DU] must have config method defined [netconf_console_path].
            xpath (str): xpath to narrow config response.
            expected_check (str): The expected_check, which can be an XPath expression or a tag name. Defaults to None
                                  If `is_xpath` is True, this should be an XPath expression.
                                  If `is_xpath` is False, this should be a tag name.
                                  If None will get full the netconf response
            id (str): component id, if none is set will do for all component of a given type. Default value is None
                      Note that with component is RU_SIM, id should be id of DU
            is_xpath (bool): True will get element by XPath
                             False will get element by tag name
        Returns:
            ret_value_netconf (list): List of values extracted from Netconf command output
        Example:
            (check by xpath) Get Config    RU    /software-inventory    expected_check=//*[local-name()='software-slot']/*[local-name()='name' and text()='slot2']/following-sibling::*[local-name()='build-version']
            (check by tag name) Get Config    RU    /software-inventory    expected_check=build-version    is_xpath=False
            (get all netconf response) Get Config    RU    /software-inventory
        """
        logger.info("Getting Netconf Configuration", also_console=True, banner=True)
        if id is None:
            if component == "RU_SIM":
                testline_components = self.testline.get_components_by_type("DU")
            else:
                testline_components = self.testline.get_components_by_type(component)
            results = []
            for testline_component in testline_components:
                result = self.get_config(
                    component, xpath, expected_check, id=testline_component.id, is_xpath=is_xpath
                )
                results.append(result)
            return results
        logger.info(
            f"====== Get Config: component: {component} - id: {id}, xpath: {xpath}",
            also_console=True,
        )
        testline_component = self.testline.get_component_by_id(id)
        nc = Global_Variables.netconf_console_path
        if component == "RU":
            sut = testline_component.ip
            oam_port = str(Global_Variables.oam_port)
            # Get ru-instance-id and add the path before xpath
            ru_instance_id = testline_component.ru_instance_id
            netconf_cmd = (
                f"{nc}netconf-console --host={sut} --user=netconf --privKeyType=rsa --privKeyFile={Global_Variables.NETCONF_PRIVATE_KEYPATH} "
                f"--port={oam_port} --get -x /aggregated-o-ru/aggregation[ru-instance={str(ru_instance_id)}]/dvs-agg-model"
                f"{xpath}"
            )
        elif component == "RU_SIM":
            if "DU" not in testline_component.type:
                raise FrameworkException(
                    f"RU_SIM component configuration must be checked from DU server. Now component id={id}, please check..."
                )
            sut = testline_component.oam_ip
            ru_sim_port = str(testline_component.ru_sim_port)
            netconf_cmd = (
                f"{nc}netconf-console --host={sut} --user=admin --password=admin "
                f"--port={ru_sim_port} --get -x {xpath}"
            )
        else:
            sut = testline_component.ip
            oam_port = str(Global_Variables.oam_port)
            netconf_cmd = (
                f"{nc}netconf-console --host={sut} --port={oam_port} --user=netconf "
                f"--privKeyType=rsa --privKeyFile={Global_Variables.NETCONF_PRIVATE_KEYPATH} --get -x {xpath}"
            )

        try:
            ret_value_netconf = utils.get_config_through_netconf(
                connection=testline_component.connection,
                netconf_cmd=netconf_cmd,
                expected_check=expected_check,
                is_xpath=is_xpath
            )
            if ret_value_netconf:
                logger.info(
                    f"Found expected check {expected_check} in Netconf response with value is: {ret_value_netconf}",
                    also_console=True
                )
                return ret_value_netconf
            else:
                raise Exception(
                    f"Could not find expected check in Netconf response due to: {ret_value_netconf}"
                )
        except Exception as e:
            raise Exception(
                f"Component: {component} - id: {id}: Could not get config due to error: {e}"
            ) from e

    def restart_gnb_via_systemctl(self,component_id: str =None, timeout: int=240) ->None:
        """
        Description:
            Used for restart all services in the server.

        Parameters:
            components_ids: any Components on the server which we want to restart , timeout: initialized with 240seconds, time to complete command.
        Returns:
            None: This function only executes the codes and does not return any value.
        """
        try:
            component_object =self.testline.get_component_by_id(component_id)
            component_object.connection.sendCommand(command="sudo systemctl restart gNB.target", timeout=timeout)
        except Exception as e:
            raise