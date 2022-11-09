"""
Copyright (c) 2020 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""
from ciscoconfparse import CiscoConfParse
from flask import Flask, render_template, request, redirect, url_for, session
import os
import meraki
import json
from pprint import pprint
import re
from collections import defaultdict
from flask_session import Session

payload = {}
organizations = {}
api = ""
payload = None

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(128)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

sw_list = []
configured_ports = defaultdict(list)
unconfigured_ports = defaultdict(list)


def meraki_config(api, sw_list, interface_dict, downlink_list):
    def config_access_port(serial, p_number, desc, active, mode,
                                  data_vlan, voice_vlan):
        try:
            dashboard = meraki.DashboardAPI(api, suppress_logging=True)
            update_status = dashboard.switch.updateDeviceSwitchPort(serial, p_number,
                                                                name=desc,
                                                                enabled=active,
                                                                type=mode,
                                                                vlan=data_vlan,
                                                                voiceVlan=voice_vlan)
            configured_ports[serial].append(p_number)
            print("Successfully configured!")
        except Exception as e:
            print("Issue configuring access port")
            print(e)
            unconfigured_ports[serial].append(p_number)

    def config_access_port_trunk(serial, p_number, desc, active, mode,
                                 native_vlan, allowed_vlan):
        try:
            dashboard = meraki.DashboardAPI(api, suppress_logging=True)
            update_status = dashboard.switch.updateDeviceSwitchPort(serial, p_number,
                                                                    name=desc,
                                                                    enabled=active,
                                                                    type=mode,
                                                                    vlan=native_vlan,
                                                                    allowedVlans=allowed_vlan,
                                                                    isolationEnabled=False,
                                                                    rstpEnabled=True,
                                                                    stpGuard="disabled",
                                                                    linkNegotiation="Auto negotiate")
            configured_ports[serial].append(p_number)
            print("Successfully configured!")
        except Exception as e:
            print("Issue configuring trunk port")
            print(e)
            unconfigured_ports[serial].append(p_number)

    def config_shut(serial, p_number, desc=None):
        try:
            dashboard = meraki.DashboardAPI(api, suppress_logging=True)
            update_status = dashboard.switch.updateDeviceSwitchPort(serial,
                                                                    p_number,
                                                                    enabled=False,
                                                                    name=desc)
            configured_ports[serial].append(p_number)
            print("Successfully configured!")
        except Exception as e:
            print("Issue shutting down port")
            print(e)
            unconfigured_ports[serial].append(p_number)

    # Loop to go through all the ports of the switches
    def loop_configure_meraki(interface_dict, downlink_list):
        try:
            y = 0
            # Loop to get all the interfaces in the interface_dict
            while y <= len(downlink_list)-1:
                x = downlink_list[y]
                print("\n----------- "+x+" -----------")
                # Check if the interface mode is configured as Access
                if interface_dict[x]['mode'] == "access":
                    if interface_dict[x]['voice_vlan'] != "":
                        voice_vlan = interface_dict[x]['voice_vlan']
                    else:
                        interface_dict[x]['voice_vlan'] = "null"

                    if interface_dict[x]['desc'] != "":
                            description = interface_dict[x]["desc"]
                    else:
                        interface_dict[x]["desc"] = ""

                    if interface_dict[x]['data_vlan'] != "":
                        data_vlan = interface_dict[x]['data_vlan']
                    else:
                        interface_dict[x]['data_vlan'] = "1"
                        data_vlan = interface_dict[x]['data_vlan']

                # Check the switch that mapped to those catalyst ports
                    sw = int(interface_dict[x]['sw_module'])
                    if sw != 0:
                        sw -= 1

                    config_access_port(sw_list[sw],
                                       interface_dict[x]['port'],
                                       interface_dict[x]["desc"],
                                       interface_dict[x]["active"],
                                       interface_dict[x]['mode'],
                                       interface_dict[x]['data_vlan'],
                                       interface_dict[x]['voice_vlan'])
                elif interface_dict[x]['mode'] == "trunk":
                    if interface_dict[x]['desc'] != "":
                            description = interface_dict[x]["desc"]
                    else:
                        interface_dict[x]["desc"] = ""

                    if interface_dict[x]['native'] != "":
                        native_vlan = interface_dict[x]['native']
                    else:
                        interface_dict[x]['native'] = "1"
                        native_vlan = interface_dict[x]['native']

                    if interface_dict[x]['trunk_allowed'] != "":
                        trunk_allow = interface_dict[x]['trunk_allowed']
                    else:
                        interface_dict[x]['trunk_allowed'] = "1-1000"

                    sw = int(interface_dict[x]['sw_module'])
                    if sw != 0:
                        sw -= 1

                    config_access_port_trunk(sw_list[sw],
                                             interface_dict[x]['port'],
                                             interface_dict[x]['desc'],
                                             interface_dict[x]['active'],
                                             interface_dict[x]['mode'],
                                             interface_dict[x]['native'],
                                             interface_dict[x]['trunk_allowed'])
                # If the interface is not configured as access or trunk just pass
                elif interface_dict[x]['mode'] == "":
                    if interface_dict[x]["active"] == "false":
                        if interface_dict[x]['desc'] != "":
                            description = interface_dict[x]['desc']
                            config_shut(sw_list[sw], interface_dict[x]['port'],
                                        description)
                        else:
                            config_shut(sw_list[sw], interface_dict[x]['port'])
                y += 1

        except:
            print("Can't find port " + str(y))
            pass

    loop_configure_meraki(interface_dict,downlink_list)

def start(API, sw_list, cisco_sw_config):
    interface_dict = {}
    # List of interfaces that are shut
    shut_interfaces = []

    def split_down_up_link(interfaces_list, gig_uplink):
        uplink_list = []
        downlink_list = []
        other_list = []

        # Creating a copy of the interface list to avoid Runtime error
        interfaces_list_copy = interfaces_list.copy()

        for key, value in interfaces_list.items():
            # TengigbitEthernet ports stright away considered as uplinks
            if key == "TenGigabitEthernet":
                for value in interfaces_list_copy["TenGigabitEthernet"]:
                    uplink_list.append(value)
        # GigbitEthernet ports to be evaluated if has 1 in subnetwork module (x/1/x) then its uplink otherwise will be downlink
            if key == "GigabitEthernet":
                for value in interfaces_list_copy["GigabitEthernet"]:
                    if value in gig_uplink:
                        Uplink_list.append(value)
                    if len(interfaces_list_copy["FastEthernet"]) > 4 and len(interfaces_list_copy["GigabitEthernet"]) < 5:
                        uplink_list.append(value)
                    elif value not in gig_uplink:
                        downlink_list.append(value)
        # FastEthernet to be checked if has more than 4 ports in the list then they all downlink
            if key == "FastEthernet" and len(interfaces_list_copy["FastEthernet"]) > 4:
                for value in interfaces_list["FastEthernet"]:
                    downlink_list.append(value)
        # Single FastEthernet interface to be considered as others
            if key == "FastEthernet" and len(interfaces_list_copy["FastEthernet"]) <= 1:
                for value in interfaces_list_copy["FastEthernet"]:
                    other_list.append(value)

            else:
                for value in interfaces_list_copy[key]:
                    if key == "TenGigabitEthernet" or key == "GigabitEthernet" or key == "FastEthernet":
                        pass
                    else:
                        other_list.append(value)
        return uplink_list, downlink_list, other_list

    # Extract out the details of the switch module and the port number
    def check(intf):
        parse = CiscoConfParse(cisco_sw_config, syntax='ios', factory=True)

        intf_rgx = re.compile(r'interface GigabitEthernet(\d+)\/(\d+)\/(\d+)$')

        for obj in parse.find_objects(intf):
            sub_module = None
            port = obj.ordinal_list[-1]
            if intf_rgx.search(obj.text) is not None:
                sub_module = obj.ordinal_list[-2]

            return port, sub_module

    def read_cisco_sw():
        # Parsing the Cisco Catalyst configuration (focused on the interface config)
        print("-------- Reading <"+cisco_sw_config+"> Configuration --------")
        parse = CiscoConfParse(cisco_sw_config, syntax='ios', factory=True)

        x = 0
        gig_uplink = []
        all_interfaces = defaultdict(list)
        # Select the interfaces
        intf = parse.find_objects('^interface')
        for intf_obj in parse.find_objects_w_child('^interface', '^\s+shutdown'):
            shut_interfaces.append(
                intf_obj.re_match_typed('^interface\s+(\S.+?)$'))
        print(f"These are the shut interfaces: {shut_interfaces}")

        for intf_obj in intf:
            # Get the interface name
            intf_name = intf_obj.re_match_typed('^interface\s+(\S.*)$')
            # Only interface name will be used to categorize different types of interfaces (downlink and uplink)
            only_intf_name = re.sub("\d+|\\/", "", intf_name)
            switch_module = intf_obj.re_match_typed(
                '^interface\s\S+?thernet+(\d)')
            test_port_numerb = intf_obj.re_match_typed(
                '^interface\s\S+?thernet+(\S+?)')

            if only_intf_name.startswith("Giga"):
                all_interfaces[only_intf_name].append(intf_name)

                interface_dict[intf_name] = {}
                interface_dict[intf_name]['sw_module'] = "1"
                interface_dict[intf_name]['desc'] = ""
                interface_dict[intf_name]['port'] = ""
                interface_dict[intf_name]['mode'] = ""
                interface_dict[intf_name]['active'] = "true"
                interface_dict[intf_name]['data_vlan'] = ""
                interface_dict[intf_name]['voice_vlan'] = ""

                try:
                    port, sub_module = check(intf_name)
                    if sub_module == 1:
                        gig_uplink.append(intf_name)

                    if switch_module == 0:
                        interface_dict[intf_name]['sw_module'] = 1
                    if not switch_module == "" and not switch_module == 0:
                        interface_dict[intf_name]['sw_module'] = switch_module

                    interface_dict[intf_name]['port'] = port
                    # check if the interface in the shutdown list then mark it as shutdown
                    if intf_name in shut_interfaces:
                        interface_dict[intf_name]['active'] = "false"

                    int_fx = intf[x].children
                    # Capture the configuration of the interface
                    for child in int_fx:
                        desc = child.re_match_typed(
                            regex=r'\sdescription\s+(\S.+)')
                        vlanv = child.re_match_typed(
                            regex=r'\sswitchport\svoice\svlan\s+(\S.*)')
                        port_mode = child.re_match_typed(
                            regex=r'\sswitchport\smode\s+(\S.+)')
                        vlan = child.re_match_typed(
                            regex=r'\sswitchport\saccess\svlan\s+(\S.*)')
                        trunk_native = child.re_match_typed(
                            regex=r'\sswitchport\strunk\snative\svlan\s+(\S.*)')
                        trunk_v_allowed = child.re_match_typed(
                            regex=r'\sswitchport\strunk\sallowed\svlan\s+(\S.*)')

                        if desc != "":
                            interface_dict[intf_name]['desc'] = desc
                        if port_mode != "":
                            interface_dict[intf_name]['mode'] = port_mode
                        if vlan != "":
                            interface_dict[intf_name]['data_vlan'] = vlan
                        if vlanv != "":
                            interface_dict[intf_name]['voice_vlan'] = vlanv
                        if trunk_native != "":
                            interface_dict[intf_name]['native'] = trunk_native
                        if trunk_v_allowed != "":
                            interface_dict[intf_name]['trunk_allowed'] = trunk_v_allowed

                except:
                    print(f"Error in ready interface {intf_name}")

            x += 1

        uplink_list, downlink_list, other_list = split_down_up_link(
            all_interfaces, gig_uplink)
        return uplink_list, downlink_list, other_list, interface_dict

    uplink_list, downlink_list, other_list, interface_dict = read_cisco_sw()
    return uplink_list, downlink_list, other_list, interface_dict


@app.route('/')
def index():
    session.clear()
    return render_template("input.html")


@app.route('/confirm', methods=["POST",])
def confirm():
    data = session["to_be_configured"]
    downlink_list = session["downlink_list"]
    api = session["api"]
    sw_list = session["sw_list"]
    # Start the meraki config migration after confirmation from the user
    meraki_config(api, sw_list, data, downlink_list)
# Check the return from the Meraki_config function and make it part of the session
    return render_template("success.html", configured_ports=configured_ports,
                           unconfigured_ports=unconfigured_ports)


@app.route('/api', methods=["POST",])
def api():
    sw_list.clear()
    configured_ports.clear()
    unconfigured_ports.clear()
    api = None
    # Get the info of the form
    session["api"] = request.form["fname"]
    uploaded_file = request.files['file']
    dir = os.path.join(os.getcwd(), "static/files")
    if uploaded_file.filename != '':
        uploaded_file.save(os.path.join(dir, uploaded_file.filename))
        with open(os.path.join(dir, uploaded_file.filename), "r") as fr:
            file_contents = fr.read()
            new_content = re.sub(" --More--\s*interface", "interface", file_contents)
            new_content = re.sub("--More--\s*", "", file_contents)


        with open(os.path.join(dir, uploaded_file.filename), "w") as fw:
            fw.write(new_content)
    sw_stack = int(request.form["member"])
    # List of the fields in the form for the switch stack
    i = 0
    while i < int(sw_stack):
        sw_list.append(request.form["member" + str(i)])
        i += 1

    session["sw_list"] = sw_list
    session["sw_file"] = os.path.join(dir, uploaded_file.filename)

    api = session["api"]
    sw_file = session["sw_file"]

    session["uplink_list"], session["downlink_list"], session["other_list"], session["interface_dict"] = start(
        api, session["sw_list"], sw_file)

    # Creating a list to select the configuration parts to push to Meraki
    to_be_configured = {}
    z = 0
    downlink_list = session["downlink_list"]
    interface_dict = session["interface_dict"]
    while z < len(downlink_list):
        interface = downlink_list[z]
        to_be_configured[interface] = interface_dict[interface]
        z += 1

    session["to_be_configured"] = to_be_configured

    return render_template("confirm.html",
                           to_be_configured=session["to_be_configured"],
                           downlink_list=session["downlink_list"])


@app.route('/drop')
def drop():
    session.clear()
    return render_template("input.html")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
