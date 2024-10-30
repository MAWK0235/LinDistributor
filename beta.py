import argparse
import urllib3
import paramiko
import ipaddress  
from time import sleep
from colorama import Fore, Style

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_all_ips_in_subnet(subnet):
    ips = [str(ip) for ip in ipaddress.IPv4Network(subnet, strict=False)]
    return ips

def establish_ssh_connection_rsa(hostname, username, private_key_path):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        private_key = paramiko.RSAKey(filename=private_key_path)
        ssh.connect(hostname, username=username, pkey=private_key)
        print(f"{Fore.YELLOW}[+] SSH connection established.{Style.RESET_ALL}")
        return ssh
    except paramiko.SSHException as e:
        print(f"{Fore.RED}[-] SSH connection failed: {str(e)}{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"{Fore.RED}[-] Unexpected error: {str(e)}{Style.RESET_ALL}")
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

            # Wait for the command to complete
            while not channel.exit_status_ready():
                sleep(1)

            output = b""
            while channel.recv_ready():
                output += channel.recv(4096)

            exit_status = channel.recv_exit_status()
            channel.close()

            command_output = output.decode()

            # If there is no output, return an empty string instead of False
            if not command_output:
                return "NULL"  # Return an empty string for no output
            return command_output
        except Exception as e:
            print(f"{Fore.RED}Failed to execute command: {str(e)}{Style.RESET_ALL}")
            sleep(1)
    return None  # Return None if ssh is None

def close_ssh_connection(ssh):
    if ssh is not None:
        ssh.close()
        print(f"{Fore.YELLOW}[+] SSH connection closed.{Style.RESET_ALL}")

def uploadAndExecTarget_ListandRSA(localExecutable, upload_Path, target_ListPath, username, rsa, port):
    try:
        with open(target_ListPath, 'r') as file:
            for target in file:
                target = target.strip()
                if '/' in target or target.endswith((".0", ".1")):
                    continue
                uploadAndExecRSA(localExecutable, upload_Path, target, username, rsa, port)
    except Exception as e:
        print(f"{Fore.RED}[-] Failed to read target list: {str(e)}{Style.RESET_ALL}")
        return False

def uploadAndExecTarget_List(localExecutable, upload_Path, target_ListPath, username, password, port):
    try:
        with open(target_ListPath, 'r') as file:
            for target in file:
                target = target.strip()
                if '/' in target or target.endswith((".0", ".1")):
                    continue
                uploadAndExecUandP(localExecutable, upload_Path, target, username, password, port)
    except Exception as e:
        print(f"{Fore.RED}[-] Failed to read target list: {str(e)}{Style.RESET_ALL}")
        return False

def uploadAndExecSubnet(localExecutable, upload_Path, target, username, password, port):
    for ip in get_all_ips_in_subnet(target):
        if ip.endswith((".0", ".1")):
            continue
        uploadAndExecUandP(localExecutable, upload_Path, ip, username, password, port)

def sftp_upload(localExecutable, upload_Path, target, username, password, port):
    try:
        transport = paramiko.Transport((target, port))
        transport.connect(username=username, password=password)

        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.put(localExecutable, upload_Path)
        sftp.close()
        transport.close()
        return True
    except Exception as e:
        print(f"{Fore.RED}[-] SFTP upload failed: {str(e)}{Style.RESET_ALL}")
        return False  # Fixed the return statement

def sftp_upload_rsa(localExecutable, upload_Path, target, username, rsa, port):
    try:
        private_key = paramiko.RSAKey(filename=rsa)
        transport = paramiko.Transport((target, port))
        transport.connect(username=username, pkey=private_key)

        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.put(localExecutable, upload_Path)
        sftp.close()
        transport.close()
        return True
    except Exception as e:
        print(f"Error during SFTP upload...your RSA key didn't work... Sorry: {e}")
        return False

def uploadAndExecUandP(localExecutable, upload_Path, target, username, password, port):
    if sftp_upload(localExecutable, upload_Path, target, username, password, port):
        ssh = establish_ssh_connection_UandP(target, username, password)
        if ssh is None:
            return
        print(f"{Fore.MAGENTA}[+] Executing executable on {target}... Please be patient, executable may take some time depending on the system... {Style.RESET_ALL}")

        with open(f'{target}_executableOut.txt', 'w') as file:
            command_output = execute_ssh_command(ssh, f"chmod +x {upload_Path} && {upload_Path} && rm -rf {upload_Path}")
            if command_output:
                file.write(command_output)
        print(f"{Fore.GREEN}[+] output file = {target}_executableOut.txt")
        print(f"{Fore.YELLOW}[*] Cleaning up {upload_Path}")

        close_ssh_connection(ssh)

def uploadAndExecRSA(localExecutable, upload_Path, target, username, rsa, port):
    if sftp_upload_rsa(localExecutable, upload_Path, target, username, rsa, port):
        ssh = establish_ssh_connection_rsa(target, username, rsa)
        if ssh is None:
            return
        print(f"{Fore.MAGENTA}[+] Executing executable on {target}... Please be patient, executable may take some time depending on the system... ")

        with open(f'{target}_executableOut.txt', 'w') as file:
            command_output, _ = execute_ssh_command(ssh, f"chmod +x {upload_Path} && {upload_Path} && rm -rf {upload_Path}")
            if command_output:
                file.write(command_output)
        print(f"{Fore.GREEN}[+] output file = {target}_executableOut.txt{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] Cleaning up {upload_Path}{Style.RESET_ALL}")

        close_ssh_connection(ssh)

def CMDExecSubnetCMD(target, username, password, rawCommand):
    print("CMDExecSubnetCMD")
    for ip in get_all_ips_in_subnet(target):
        if ip.endswith((".0", ".1")):
            continue
        rawCommandLinuxUandP(ip,username,password,rawCommand)

def CMDExecTarget_List(target_ListPath, username, password, rawCommand):
    print("CMDExecTarget_List")
    try:
        with open(target_ListPath, 'r') as file:
            for target in file:
                target = target.strip()  # Remove leading/trailing whitespaces
                if '/' in target or target.endswith(".0") or target.endswith(".1"):
                    continue
                rawCommandLinuxUandP(target,username,password,rawCommand)
    except Exception as e:
        print(f"{Fore.RED}[-] Failed to read target list: {str(e)}{Style.RESET_ALL}")
        return False
    
def CMDExecTarget_ListandRSA(target_ListPath, username, RSA, rawCommand):
    print("CMDExecTarget_ListandRSA")
    try:
        with open(target_ListPath, 'r') as file:
            for target in file:
                target = target.strip()  # Remove leading/trailing whitespaces
                if '/' in target or target.endswith(".0") or target.endswith(".1"):
                    continue
    except Exception as e:
        print(f"{Fore.RED}[-] Failed to read target list: {str(e)}{Style.RESET_ALL}")
        return False

def CMDExecUandP(target, username, password, rawCommand):
    print("CMDExecUandP")
    rawCommandLinuxUandP(target,username,password,rawCommand)

def CMDExecRSA(target, username, rsa, rawCommand):
    
    ssh = establish_ssh_connection_rsa(target, username, rsa)
    if ssh is None:
        return
    with open(f'{target}_executableOut.txt', 'w') as file:
        command_output, _ = execute_ssh_command(ssh, rawCommand)
        print(command_output)
        if command_output:
            file.write(command_output)
    print(f"{Fore.GREEN}[+] output file = {target}_executableOut.txt{Style.RESET_ALL}")
    close_ssh_connection(ssh)

def rawCommandLinuxUandP(target, username, password, rawCommand):
    try:
        
        print(f'{Fore.BLUE}[*] attempting connection on {target}.....')
        ssh = establish_ssh_connection_UandP(target, username, password)
        if ssh == None:
            return
        
        
        with open(f'{target}out.txt', 'w') as file:
            print("executing: " + rawCommand)
            command_output = execute_ssh_command(ssh, rawCommand)
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
    print(f"{Fore.BLUE}###############################################################################{Style.RESET_ALL}")
    print(f"{Fore.RED}A custom script for distributing in mass! ")
    print(f"{Fore.BLUE}###############################################################################{Style.RESET_ALL}")
    print("")
    parser = argparse.ArgumentParser(usage= "sudo Distributor.py -h")
    parser.add_argument('-Linux',dest='Linux', help="Target linux machines using SSH",action='store_true')
    parser.add_argument('-Windows',dest='Windows', help="Target windows machines using evil-winrm",action='store_true')
    parser.add_argument('-c', dest='rawCommand',help= "execute a singular command accross systems and return output",action='store_true')
    parser.add_argument('-le', dest='localExecutable',help= "Path to the executable file you would like to distribute")
    parser.add_argument('-up', dest='upload_Path', help= "The directory to write executable to", default="/tmp")
    parser.add_argument('-t', dest='target', help="The target or subnet you would like to target")
    parser.add_argument('-tl', dest='target_List', help="The target list in the form of a file")
    parser.add_argument('-u', dest='username', help= "The username to authenticate with ")
    parser.add_argument('-p', dest='password', help= "The password to authenticate with ")
    parser.add_argument('-R', dest='RSA', help= "The RSA key to authenticate with ")
    parser.add_argument('-P', dest='port', help= "The SSH port", default=22)
    args = parser.parse_args()
    
    #arguments for linux systems
    if args.Linux:
        if not args.username:
            print("Error: -u (username) is required for Linux targeting.")
            exit(1)
        
        if args.target is None and args.target_List is None:
            print("Error: You must specify either -t (target) or -tl (target list) for Linux targeting.")
            exit(1)

        if args.password is None and args.RSA is None:
            print("Error: You must specify either -p (password) or -R (RSA key) for Linux targeting.")
            exit(1)

        if args.rawCommand is None:
            if args.localExecutable is None:
                print("Error: -le (localExecutable) is required when not using a raw command.")
                exit(1)
            
        # Continue with execution if all required flags are satisfied
        print("Targeting Linux...")

        if args.target is not None and '/' in args.target: 
            if args.rawCommand:
                rawCommand = input("[*] CMD: ")
                CMDExecSubnetCMD(args.target, args.username, args.password, rawCommand)
            else:
                uploadAndExecSubnet(args.localExecutable, args.upload_Path, args.target, args.username, args.password, args.port)
        
        elif args.password is not None:
            if args.target_List is not None:
                if args.rawCommand:
                    rawCommand = input("[*] CMD: ")
                    CMDExecTarget_List(args.target_List, args.username, args.password, rawCommand)
                else:
                    uploadAndExecTarget_List(args.localExecutable, args.upload_Path, args.target_List, args.username, args.password, args.port)
            else:
                if args.rawCommand:
                    rawCommand = input("[*] CMD: ")
                    CMDExecUandP(args.target, args.username, args.password, rawCommand)
                else:
                    uploadAndExecUandP(args.localExecutable, args.upload_Path, args.target, args.username, args.password, args.port)

        elif args.RSA is not None:
            if args.target_List is not None:
                if args.rawCommand:
                    rawCommand = input("[*] CMD: ")
                    CMDExecTarget_ListandRSA(args.target_List, args.username, args.RSA, rawCommand)
                else:
                    uploadAndExecTarget_ListandRSA(args.localExecutable, args.upload_Path, args.target_List, args.username, args.RSA, args.port)
            else:
                if args.rawCommand:
                    rawCommand = input("[*] CMD: ")
                    CMDExecRSA(args.target, args.username, args.RSA, rawCommand)
                else:
                    uploadAndExecRSA(args.localExecutable, args.upload_Path, args.target, args.username, args.RSA, args.port)

        else:
            print("Error: How did you get here? I must not have planned for this event.... use -h")

    else:
        print("Error: Please use -h for help.")

