#!/usr/bin/env python3
import yaml
import docker
import psutil
import os
import argparse
import logging

dockercli = docker.from_env()
parser = argparse.ArgumentParser()
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)


parser.add_argument('--start', type=int, required=True, help='Start ID of Vimeo video.')
parser.add_argument('--end', type=int, required=True, help='Last ID of Vimeo video.')
args = parser.parse_args()


def load_config(config_file):
    with open(config_file, 'r') as f:
        try:
            return yaml.load(f, Loader=yaml.FullLoader)
        except yaml.YAMLError as err:
            logging.error(err)

def create_network(name):
    if len(dockercli.networks.list(name)) == 0:
        dockercli.networks.create(name, driver="bridge")
    else:
        logging.info("Network already exists!!")

def run_container(service, replica, **kwargs):
    service_name="{}_{}".format(service, replica)
    ports_dict = {}

    # The named argument for the docker library is called NETWORK and only accept one item
    kwargs['network'] = kwargs.pop('networks')
    kwargs['network'] = kwargs["network"][0]
    
    # The docker library only accepts ports as a dictionary
    if "ports" in kwargs:
        for p in kwargs["ports"]:
            host_port=p.split(':')[0]
            container_port="{}/tcp".format(p.split(':')[1])
            ports_dict[container_port] = host_port

    # If the volume is a relative path
    if "volumes" in kwargs:
        index = 0
        while index < len(kwargs["volumes"]):
            v = kwargs["volumes"][index]
            host_dir=v.split(':')[0]
            if (host_dir.split('/')[0] == ".") or (host_dir.split('/')[0] == "$PWD"):
                absolute_dir="{}/{}".format(os.getcwd(),host_dir.split('/')[1:][0])
                string_volume="{}:{}".format(absolute_dir, v.split(':')[1])
                kwargs["volumes"][index]=string_volume
            index += 1

    # Method run doesn't accept some compose options
    things_remove = ("deploy", "depends_on", "ports")
    for key in things_remove:
        kwargs.pop(key, None)

    logging.info("Running container: {}".format(service_name))
    if "environment" in kwargs:
        logging.debug(kwargs["environment"])
    dockercli.containers.run(name=service_name, ports=ports_dict, **kwargs, detach=True)

def wait_release_resource():
    while True:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory()[2]
        logging.info("Current CPU: {}% - Current Memory: {}%".format(cpu_percent, memory_percent))
        
        if (cpu_percent < 85.0) and (memory_percent < 90.0):
            break
        
        logging.info("Trying to unallocate some resources!")
        dockercli.containers.prune()
        dockercli.images.prune()
        dockercli.volumes.prune()

def find_start_end(arg_start, arg_end, replica, instance):
    div=int((arg_end - arg_start)/replica)
    x = range(arg_start, arg_end, div)

    return ['VIMEO_ID_START={}'.format(x[instance]), 'VIMEO_ID_END={}'.format(x[instance]+div)]


config = load_config("./docker-compose.yml")
net_keys = [*config["networks"]]


for netname in net_keys:
    logging.info("Creating network {}!".format(netname))
    create_network(netname)
    for service, attr in config["services"].items():
        for instance in range(0, attr["deploy"]["replicas"]):
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory()[2]
            if cpu_percent >= 85.0 or memory_percent >= 90.0:
                wait_release_resource()

            if ("environment" in attr) and service == 'scraper':
                attr["environment"] = find_start_end(args.start, args.end, attr["deploy"]["replicas"], instance)

            run_container(service, instance, **attr)