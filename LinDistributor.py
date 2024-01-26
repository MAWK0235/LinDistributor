import argparse
import urllib3
import paramiko
import ipaddress  
from time import sleep
from colorama import Fore, Style

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def uploadAndExecTarget_ListandRSA(local_LinPath, upload_Path, target_ListPath, username, rsa, port):
    try:
        with open(target_ListPath, 'r') as file:
            for target in file:
                target = target.strip()  # Remove leading/trailing whitespaces
                if '/' in target or target.endswith(".0") or target.endswith(".1"):
                    continue
                uploadAndExecRSA(local_LinPath, upload_Path, target, username, rsa, port)
    except Exception as e:
        print(f"{Fore.RED}[-] Failed to read target list: {str(e)}{Style.RESET_ALL}")
        return False

def uploadAndExecTarget_List(local_LinPath, upload_Path, target_ListPath, username, password, port):
    try:
        with open(target_ListPath, 'r') as file:
            for target in file:
                target = target.strip()  # Remove leading/trailing whitespaces
                if '/' in target or target.endswith(".0") or target.endswith(".1"):
                    continue
                uploadAndExecUandP(local_LinPath, upload_Path, target, username, password, port)
    except Exception as e:
        print(f"{Fore.RED}[-] Failed to read target list: {str(e)}{Style.RESET_ALL}")
        return False

def get_all_ips_in_subnet(subnet):

    ips = [str(ip) for ip in ipaddress.IPv4Network(subnet, strict=False)]
    return ips

def uploadAndExecSubnet(local_LinPath, upload_Path, subnet, username, password, port):
    for ip in get_all_ips_in_subnet(subnet):
        if ip.endswith(".0") or ip.endswith(".1"):
            continue
        uploadAndExecUandP(local_LinPath, upload_Path, ip, username, password, port)




def establish_ssh_connection_rsa(hostname, username, private_key_path):
    ssh = paramiko.SSHClient()
    private_key = paramiko.RSAKey(filename=private_key_path)
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname, username=username, pkey=private_key)
        print(f"{Fore.YELLOW}[+] SSH connection established.{Style.RESET_ALL}")
        return ssh
    except Exception as e:
        print(f"{Fore.RED}[-] Failed to establish SSH connection: {str(e)}{Style.RESET_ALL}")
        return None

def establish_ssh_connection_UandP(hostname, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname, username=username, password=password, timeout=10)
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

def sftp_upload(local_LinPath,upload_Path,target,username,password,port):
    try:
        transport = paramiko.Transport((target, port))
        transport.connect(username=username, password=password)

        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.put(local_LinPath, upload_Path)
        sftp.close()
        transport.close()
    
    except Exception as e:
        return False
def sftp_upload_rsa(local_LinPath, upload_Path, target, username, rsa, port):
    try:
        private_key = paramiko.RSAKey(filename=rsa)
        transport = paramiko.Transport((target, port))
        transport.connect(username=username, pkey=private_key)

        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.put(local_LinPath, upload_Path)
        sftp.close()
        transport.close()

    except Exception as e:
        print(f"Error during SFTP upload...your RSA key didnt work...Sorry..: {e}")
        return False

    
def uploadAndExecUandP(local_LinPath, upload_Path, target, username, password, port):
    try:
        sftp_upload(local_LinPath, upload_Path, target, username, password, port)
        
        ssh = establish_ssh_connection_UandP(target, username, password)
        if ssh == None:
            return
        print(f"{Fore.MAGENTA}[+] Executing linpeas on {target}... Please be patient, linpeas may take some time depending on the system... ")
        
        with open(f'{target}linpeasOut.txt', 'w') as file:
            command_output = execute_ssh_command(ssh, f"chmod +x {upload_Path} && {upload_Path} && rm -rf {upload_Path}")
            
            #Debug Wait for the command to finish
           # while not command_output.strip():
           #     sleep(1)
            #    command_output = execute_ssh_command(ssh, "")  # Check if there is any output
                
            file.write(command_output)
        print(f"{Fore.GREEN}[+] output file = {target}linpeasOut.txt")
        print(f"{Fore.YELLOW}[*] Cleaning up {upload_Path}")
        
        close_ssh_connection(ssh)
    except Exception as e:
        return False
def uploadAndExecRSA(local_LinPath, upload_Path, target, username, rsa, port):
    try:
        sftp_upload_rsa(local_LinPath, upload_Path, target, username, rsa, port)
        
        ssh = establish_ssh_connection_rsa(target, username, rsa)
        if ssh == None:
            return
        print(f"{Fore.MAGENTA}[+] Executing linpeas on {target}... Please be patient, linpeas may take some time depending on the system... ")
        
        with open(f'{target}linpeasOut.txt', 'w') as file:
            command_output = execute_ssh_command(ssh, f"chmod +x {upload_Path} && {upload_Path} && rm -rf {upload_Path}")
            
            #Debug Wait for the command to finish
           # while not command_output.strip():
           #     sleep(1)
            #    command_output = execute_ssh_command(ssh, "")  # Check if there is any output
                
            file.write(command_output)
        print(f"{Fore.GREEN}[+] output file = {target}linpeasOut.txt")
        print(f"{Fore.YELLOW}[*] Cleaning up {upload_Path}")
        
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
    print(f"{Fore.RED}A custom script for running linpeas in mass! (Yes the script cleans up as well!)")
    print(f"{Fore.BLUE}###############################################################################")
    print("")
    parser = argparse.ArgumentParser(description="AutoPwn Script for Bizness HTB machine", usage= "sudo LinDistributor.py -h")
    parser.add_argument('-lp', dest='local_LinPath',help= "Path to the linpeas file you would like to distribute ", required=True)
    parser.add_argument('-up', dest='upload_Path', help= "The directory to write linpeas to", required = True)
    parser.add_argument('-t', dest='target', help="The target or subnet you would like to run linpeas on")
    parser.add_argument('-tl', dest='target_List', help="The target list to run linpeas on")
    parser.add_argument('-u', dest='username', help= "The username to authenticate with ", required=True)
    parser.add_argument('-p', dest='password', help= "The password to authenticate with ")
    parser.add_argument('-R', dest='RSA', help= "The RSA key to authenticate with ")
    parser.add_argument('-P', dest='port', help= "The SSH port", default=22)
    
    args = parser.parse_args()
    

    if args.target != None and '/' in args.target: 
        uploadAndExecSubnet(args.local_LinPath, args.upload_Path, args.target, args.username, args.password, args.port)
    elif args.password is not None:
        if args.target_List is not None:
        
            uploadAndExecTarget_List(args.local_LinPath, args.upload_Path, args.target_List, args.username, args.password, args.port)
        else:
            uploadAndExecUandP(args.local_LinPath, args.upload_Path, args.target, args.username, args.password, args.port)
    elif args.RSA != None:
        if args.target_List is not None:
            uploadAndExecTarget_ListandRSA(args.local_LinPath, args.upload_Path, args.target_List, args.username, args.RSA, args.port)
        else:
            uploadAndExecRSA(args.local_LinPath, args.upload_Path, args.target, args.username, args.RSA, args.port)

    else:
        print("how did you get here? I must not have planned for this event.... use -h")
