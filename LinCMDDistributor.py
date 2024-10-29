import argparse
import urllib3
import paramiko
import ipaddress  
from time import sleep
from colorama import Fore, Style

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



def uploadAndExecTarget_List(target_ListPath, username, password,command):
    try:
        with open(target_ListPath, 'r') as file:
            for target in file:
                target = target.strip()  # Remove leading/trailing whitespaces
                if '/' in target or target.endswith(".0") or target.endswith(".1"):
                    continue
                uploadAndExecUandP(target, username, password,command)
    except Exception as e:
        print(f"{Fore.RED}[-] Failed to read target list: {str(e)}{Style.RESET_ALL}")
        return False

def get_all_ips_in_subnet(subnet):

    ips = [str(ip) for ip in ipaddress.IPv4Network(subnet, strict=False)]
    return ips

def establish_ssh_connection_UandP(hostname, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname, username=username, password=password, timeout=20)
        print(f"{Fore.YELLOW}[+] SSH connection established.{Style.RESET_ALL}")
        return ssh
    except Exception as e:
        print(f"{Fore.RED}[-] Failed to establish SSH connection: {str(e)}{Style.RESET_ALL}")
        return None

def execute_ssh_command(ssh, command):
    if ssh is not None:
        try:
            channel = ssh.get_transport().open_session()
            channel.exec_command(command)
            while not channel.exit_status_ready() or not channel.recv_ready():
                sleep(1)

            output = b""
            while channel.recv_ready():
                output += channel.recv(4096)
            while not channel.exit_status_ready():
                sleep(1)
            exit_status = channel.recv_exit_status()
            channel.close()
            command_output = output.decode()
            return command_output
        except Exception as e:
            print(f"{Fore.RED}Failed to execute command: {str(e)}{Style.RESET_ALL}")
            sleep(1)
    return False

def close_ssh_connection(ssh):
    if ssh is not None:
        ssh.close()
        print(f"{Fore.YELLOW}[+] SSH connection closed.{Style.RESET_ALL}")
        sleep(1)
  
def uploadAndExecUandP(target, username, password,command):
    try:
        
        print(f'{Fore.BLUE}[*] attempting connection on {target}.....')
        ssh = establish_ssh_connection_UandP(target, username, password)
        if ssh == None:
            return
        
        
        with open(f'{target}out.txt', 'w') as file:
            command_output = execute_ssh_command(ssh, command)
            file.write(command_output)
        print(f"{Fore.GREEN}[+] output file = {target}out.txt")     
        close_ssh_connection(ssh)
    except Exception as e:
        return False




if __name__ == '__main__':
    ascii_art = f"""{Fore.LIGHTRED_EX}
███╗   ███╗ █████╗ ██╗    ██╗██╗  ██╗    ███████╗ ██████╗██████╗ ██╗██████╗ ████████╗███████╗
████╗ ████║██╔══██╗██║    ██║██║ ██╔╝    ██╔════╝██╔════╝██╔══██╗██║██╔══██╗╚══██╔══╝██╔════╝
██╔████╔██║███████║██║ █╗ ██║█████╔╝     ███████╗██║     ██████╔╝██║██████╔╝   ██║   ███████╗
██║╚██╔╝██║██╔══██║██║███╗██║██╔═██╗     ╚════██║██║     ██╔══██╗██║██╔═══╝    ██║   ╚════██║
██║ ╚═╝ ██║██║  ██║╚███╔███╔╝██║  ██╗    ███████║╚██████╗██║  ██║██║██║        ██║   ███████║
╚═╝     ╚═╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚═╝  ╚═╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝╚═╝        ╚═╝   ╚══════╝
     {Style.RESET_ALL}                                                                                      
    """
    print(ascii_art)
    print(f"{Fore.BLUE}###############################################################################")
    print(f"{Fore.RED}A custom script for running linux commands in mass!")
    print(f"{Fore.BLUE}###############################################################################")
    print("")
    parser = argparse.ArgumentParser(description="yo momma", usage= "sudo LinDistributor.py -h")
    

    parser.add_argument('-tl', dest='target_List', help="The target list to run linpeas on")
    parser.add_argument('-u', dest='username', help= "The username to authenticate with ", required=True)
    parser.add_argument('-p', dest='password', help= "The password to authenticate with ") 
    args = parser.parse_args()
    
    uploadAndExecTarget_List(args.target_List, args.username, args.password, input("[*] command to execute: "))