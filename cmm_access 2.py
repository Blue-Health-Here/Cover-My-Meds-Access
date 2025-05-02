from datetime import datetime, timedelta, timezone
import email
import imaplib
import re
import sys
import time
import requests
from seleniumwire import webdriver as swebdriver
from selenium import webdriver as webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.keys import Keys
from specific_pahrma_list import Specific_Pharmacies
from specific_prescriber_list import Specific_Prescribers

pharmacy_class = Specific_Pharmacies()
prescriber_class = Specific_Prescribers()

cmm_usernmae = None
cmm_pass = None
gmail_username = None
gmail_pass = None
sender_email = None
webhook_url = None
mailbox_email = None
mailbox_pass = None
aliases = None
zip_code = None
session_id = None

class CoverMyMedsAutomate:
    def __init__(self):
        self.sender_emai = "noreply@okta.com"
        self.api_key = 'patZ7tm6bwQTaXc9C.fb1a46425d9249b0b90aa9db58b532259d28668d16938bb133a99990e3b1214d'
        self.base_id = 'appdrQf5f0GaAFOrP'
        self.table_name = 'Master'
        self.proxy_username = '1383e338b64de1311514'
        self.proxy_password = 'd05ddd7ffa661543'
        self.proxy_address = 'gw.dataimpulse.com'
        self.proxy_port = '823'
        self.pharma_data = pharmacy_class.pahrma_data
        self.pres_data = prescriber_class.pres_data
        self.cmm_url = 'https://oidc.covermymeds.com/login?return_url=%2Foauth%2Fauthorize%3Fclient_id%3D-QXKSuZr5mOEba23vs1QzqnlFiQFwSVj70BG2nrD3SI%26nonce%3D7b82b71ca3ff824a228df47f465ad507%26redirect_uri%3Dhttps%253A%252F%252Faccount.covermymeds.com%252Fauth%252Fcmm_oidc%252Fcallback%26response_type%3Dcode%26scope%3Dopenid%2520profile%2520email%2520offline_access%26state%3D1020c72af312fafc05b4c82d43df95fb'

    def CMM_login(self, driver):
        global cmm_usernmae, cmm_pass, gmail_username, gmail_pass
        try:
            driver.get(self.cmm_url)
            print(cmm_usernmae)

            username_field = driver.find_element(By.ID, "username")
            password_field = driver.find_element(By.ID, "password")
            login_btn = driver.find_element(By.ID, 'login-button')
            
            username_field.send_keys(cmm_usernmae)
            password_field.send_keys(cmm_pass)
            login_btn.click()


            wait = WebDriverWait(driver, 30)
            send_email_btn = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".button.button-primary")))
            send_email_btn.click()

            code_button = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".button-link.enter-auth-code-instead-link")))
            code_button.click()

            print('Status: success, msg: Login successful')
            return {'status': 'success', 'msg': 'Login successful'}
        except Exception as ex:
            print(f'Status: error, msg: Exception occurs at CMM_login function, data: {ex}')
            return {'status': 'error', 'msg': 'Exception occurs at CMM_login function', 'data': str(ex)}
    
    def fetch_otp_mailbox(self):
        global cmm_usernmae, cmm_pass, gmail_username, gmail_pass, sender_email, webhook_url, mailbox_email, mailbox_pass, aliases
        try:
            mail = imaplib.IMAP4_SSL("imap.mailbox.org")  
            mail.login(mailbox_email, mailbox_pass)
            mail.select("inbox")

            today_utc = datetime.now(timezone.utc)
            yesterday_utc = today_utc - timedelta(days=1)
            
            today_pkt = today_utc + timedelta(hours=5)

            date_format = "%d-%b-%Y"
            yesterday_str = yesterday_utc.strftime(date_format)
            today_pkt_str = today_pkt.strftime(date_format)

            # status, messages = mail.search(None, f'(FROM "{self.sender_emai}" ON {today_pkt_str})')
            status, messages = mail.search(None, f'(FROM "{self.sender_emai}" TO "{aliases}" SINCE {yesterday_str})')
            email_ids = messages[0].split()

            # Check if no emails are found
            if not email_ids:
                return None

            # Fetch the latest email
            latest_email_id = email_ids[-1]
            res, msg = mail.fetch(latest_email_id, "(RFC822)")

            # Function to extract code from email body
            def extract_code(body):
                match = re.search(r'(\d{6})', body)
                if match:
                    return match.group(1)
                return None

            for response_part in msg:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                code = extract_code(body)
                                if code:
                                    print("Mailbox Code:", code)
                                    return {'status': 'success', 'msg': 'OTP Fetched!', 'data': code}
                    else:
                        if msg.get_content_type() == "text/plain":
                            body = msg.get_payload(decode=True).decode()
                            code = extract_code(body)
                            if code:
                                print("Mailbox Code:", code)
                                return {'status': 'success', 'msg': 'OTP Fetched!', 'data': code}
            mail.close()
            mail.logout()
        except Exception as ex:
            print(f'status: error, msg: Exception occurs at fetch_otp_mailbox function, data: {ex}')
            return {'status': 'error', 'msg': 'Exception occurs at fetch_otp_mailbox function', 'data': str(ex)}

    def fetch_otp_gmail(self):
        global cmm_usernmae, cmm_pass, gmail_username, gmail_pass, sender_email, webhook_url
        try:
            # Connect to the server and go to its inbox
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(gmail_username, gmail_pass)
            mail.select("inbox")

            today_utc = datetime.now(timezone.utc)
            yesterday_utc = today_utc - timedelta(days=1)

            today_pkt = today_utc + timedelta(hours=5)

            date_format = "%d-%b-%Y"
            yesterday_str = yesterday_utc.strftime(date_format)
            today_pkt_str = today_pkt.strftime(date_format)

            # status, messages = mail.search(None, f'(FROM "{self.sender_emai}" ON {today_pkt_str})')
            status, messages = mail.search(None, f'(FROM "{self.sender_emai}" SINCE {yesterday_str})')
            email_ids = messages[0].split()

            # Check if no emails are found
            if not email_ids:
                return None

            # Fetch the latest email
            latest_email_id = email_ids[-1]
            res, msg = mail.fetch(latest_email_id, "(RFC822)")

            # Function to extract code from email body
            def extract_code(body):
                match = re.search(r'(\d{6})', body)
                if match:
                    return match.group(1)
                return None

            for response_part in msg:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                code = extract_code(body)
                                if code:
                                    print("Code:", code)
                                    # print(f'status: success, msg: OTP Fetched!, data: {match.group()}')
                                    return {'status': 'success', 'msg': 'OTP Fetched!', 'data': code}
                    else:
                        if msg.get_content_type() == "text/plain":
                            body = msg.get_payload(decode=True).decode()
                            code = extract_code(body)
                            if code:
                                print("Code:", code)
                                return {'status': 'success', 'msg': 'OTP Fetched!', 'data': code}
            mail.close()
            mail.logout()
        except Exception as ex:
            print(f'status: error, msg: Exception occurs at fetch_otp_gmail function, data: {ex}')
            return {'status': 'error', 'msg': 'Exception occurs at fetch_otp_gmail function', 'data': str(ex)}

    def fetch_otp_outlook(self):
        global cmm_usernmae, cmm_pass, gmail_username, gmail_pass, initiator, sender_email, webhook_url
        try:
            # print(webhook_url)
            response = requests.post(webhook_url)

            if response.status_code == 200:
                try:
                    email_data = response.json()
                    # print("Email Details:")
                    # print(email_data)
                    email_content = email_data.get('content', '')
                    match = re.search(r'\b\d{6}\b', email_content)
                    if match:
                        print(f'status: success, msg: OTP Fetched!, data: {match.group()}')
                        return {'status': 'success', 'msg': 'OTP Fetched!', 'data': match.group()}
                    else:
                        print(f'status: error, msg: No match Found!')
                        return {'status': 'error', 'msg': 'No match Found!'}
                except ValueError as ve:
                    print(f'status: error, msg: Response not in json format!, data: {ve}')
                    return {'status': 'error', 'msg': 'Response not in json format!', 'data': str(ve)}
            else:
                print(f'status: error, msg: Response Status code is not 200!')
                return {'status': 'error', 'msg': 'Response Status code is not 200!'}
        except Exception as ex:
            print(f'status: error, msg: Exception occurs at fetch_otp_outlook function, data: {ex}')
            return {'status': 'error', 'msg': 'Exception occurs at fetch_otp_outlook function', 'data': str(ex)}
    
    def main(self):
        # try:
        global cmm_usernmae, cmm_pass, gmail_username, gmail_pass, sender_email, webhook_url, mailbox_email, mailbox_pass, aliases, zip_code, session_id
        while True:
            cmm_usernmae = None
            cmm_pass = None
            gmail_username = None
            gmail_pass = None
            sender_email = None
            webhook_url = None
            mailbox_email = None
            mailbox_pass = None
            aliases = None
            zip_code = None
            session_id = None

            presc_mapping = {
                'a': 'makar, gamil',
                'b': 'majid, saniea',
                'c': 'dresdner, michael',
                'd': 'denoble, shaghayegh',
                'e': 'hainer, meg',
                'f': 'barness, michael',
                'g': 'mazzoccoli, vito',
                'h': 'saitta, jacqueline',
                'i': 'zhang, yuqing',
                'j': 'shen, angela',
                'k': 'zhou, jin',
                'l': 'cao, ning',
                'm': 'chan, sing',
                'n': 'khan, saima',
                'o': 'fox, alissa b',
                'p': 'ferrara, elizabeth',
                'q': 'mian, bilal',
                'r': 'rivas, jimena',
                's': 'calderon, rosa',
                't': 'onyeador o, beatrice',
                'u': 'revoredo, fred',
                'v': 'marani dicovski, marcela',
                'w': 'agarwala, ajay',
                'x': 'shah, sulay',
                'y': 'fowler, emilie',
                'z': 'nizam, mohammed', 
                'aa': 'powell, michelle',
                'ab': 'vukic, mario',
                'ac': 'rojas, milagros', 
                'ad': 'jafri, syed',
                'ae': 'ali, shaik',
                'af': 'wilson-tarpeh, ellen',
                'ag': 'brown, dwayne',
                'ah': 'schlakman, brandon',
                'ai': 'friedberg, andrea',
                'aj': 'mellul, david',
                'ak': 'weinstock, brett',
                'al': 'rosenfeld, deborah',
                'am': 'wuzzardo, brandon',
                'an': 'florio suskevic, katherine',
                'ao': 'mcnally, kristie',
                'ap': 'patel, pradip',
                'aq': 'pintauro, kellyann',
                'ar': 'parikh, haley',
                'as': 'tran, jacques',
                'at': 'yu, may',
                'au': 'cruz, taisha',
                'av': 'pintauro, robert',
                'aw': 'som, sumit',
                'ax': 'humera, rafath',
                'ay': 'szymanek, erica',
                'az': 'khan, intazam',
                'ba': 'moeller, chaim',
                'bb': 'ilyayeva, stella',
                'bc': 'izrayelit, leonid',
                'bd': 'fashakin, emmanuel',
                'be': 'mannan, bilal',
                'bf': 'bognet, joseph',
                'bg': 'westgate, danielle',
                'bh': 'romascavage, frank',
                'bi': 'kaufman, kathy',
                'bj': 'swartz, stephen',
                'bk': 'mazzocchi, dominic',
                'bl': 'van der sluis, ralf',
                'bm': 'movva, srinivasa',
                'bn': 'bozzi, meredith',
                'bo': 'demarco, lauren',
                'bp': 'bijal, dave',
                'bq': 'maykish, susan',
                'br': 'khesin, yevgeniy',
                'bs': 'alemu, ermiyas',
                'bt': 'chi, danny',
                'bu': 'morgan, dorcas',
                'bv': 'belman, anna',
                'bw': 'enuma, celestina',
                'bx': 'cervone, joseph',
                'by': 'kochhar, rikhil',
                'bz': 'lira, lorraine',
                'ca': 'vitale, joseph',
                'cb': 'fellus, jonathan',
                'cc': 'rapadas, cathryn',
                'cd': 'haghverdi, mojdeh',
                'ce': 'marquinez, anthony',
                'cf': 'cadesky, adam',
                'cg': 'kapoor, anil',
                'ch': 'pildysh, inna',
                'ci': 'siddiqui, anila',
                'cj': 'sammartino, robert',
                'ck': 'jing, tong',
                'cl': 'hitchner, allison',
                'cm': 'hyun, jae',
                'cn': 'tan, wu',
                'co': 'peters, dana',
                'cp': 'solaimanzadeh, sima',
                'cq': 'noor, emad',
                'cr': 'leone, matthew',
                'cs': 'mikolaenko, ivan',
                'ct': 'saw, thazin',
                'cu': 'antebi, yael',
                'cv': 'korogluyev, mikhail',
                'cw': 'kremen, inna',
                'cx': 'gupta, manjari',
                'cy': 'owunna, uzoma',
                'cz': 'gross, renee',
                'da': 'gleason, abigail',
                'db': 'brown, jennifer',
                'dc': 'tung, william',
                'dd': 'nieves, jessica',
                'de': 'schuler, anna',
                'df': 'hussaini, batool',
                'dg': 'escobar, paola',
                'dh': 'frenkel, violina',
                'di': 'shahid, haroon'
            }

            pharma_mapping = {
                '1': 'silver care pharmacy',
                '2': 'barons',
                '3': 'arrow pharmacy',
                '4': 'crossroads specialty pharmacy',
                '5': 'island care pharmacy',
                '6': 'matawan pharmacy',
                '7': 'silver pharmacy',
                '8': 'pharmacy 77 ny',
                '9': 'quisqueya pharmacy',
                '10': 'st joseph pharmacy',
                '11': 'peoples pharmacy',
                '12': 'rex pharmacy',
                '13': 'lake shore pharmacy',
                '14': 'mypharmacy admin',
                '15': 'white horse pharmacy',
                '16': 'greenfield pharmacy',
                '17': 'morris park pharmacy',
                '18': 'vanguard pharmacy',
                '19': 'prospect care',
                '20': 'burlington pharmacy',
                '21': 'clinton pharmacy',
                '22': 'crescent pharmacy',
                '23': 'ultra care',
                '24': 'iqra pharmacy',
                '25': 'twin parks pharmacy',
                '26': 'main st. pharmacy',
                '27': 'elixirx apothecary',
                '28': 'broad specialty pharmacy',
                '29': 'professional center pharmacy',
                '30': 'nostrumrx pharmacy',
                '31': 'broadway health pharmacy',
                '32': 'penlar pharmacy',
                '33': 'mt prospect pharmacy',
                '34': 'goodrx',
                '35': 'familycare nj',
                '36': 'grace pharmacy',
                '37': 'sante integrative pharmacy',
                '38': 'vcare rx',
                '39': 'bestchoice rx',
                '40': 'health plus',
                '41': 'nys pharmacy',
                '42': 'lifeline baltimore pharmacy',
                '43': 'medics pharmacy',
                '44': 'psp',
                '45': 'international pharmacy',
                '46': 'emmaus',
                '47': 'white plains pharmacy',
                '48': 'hub specialty pharmacy',
                '49': 'west hartford apothecary',
                '50': 'city meds',
                '51': 'ramtown pharmacy',
                '52': 'albini pharmacy',
                '53': 'modern pharmacy',
                '54': 'shorham drugs',
                '55': 'quality pharmacy',
                '56': 'admin medlife',
                '57': 'readyrx pharmacy',
                '58': 'star care pharmacy',
                '59': 'family care ny',
                '60': 'tammycare',
                '61': 'skylands family pharmacy',
                '62': 'bristol pharmacy',
                '63': 'milbrook pharmacy ',
                '64': 'asbell pharmacy',
                '65': 'a- rst rome pharmacy',
                '66': 'apex health pharmacy',
                '67': 'firo pharmacy',
                '68': 'rockaway drug rx pharmacy',
                '69': 'star pharmacy',
                '70': 'eagle rock'
            }

            pharmacies = [
                "Silver Care Pharmacy", "Barons Pharmacy", "Arrow Pharmacy", "Crossroads Specialty Pharmacy",
                "Island Care Pharmacy/Supa Pharmacy", "Matawan Pharmacy/Admin Matawan", "Silver Pharmacy", 
                "Pharmacy 77 NY", "Quisqueya Pharmacy", "St Joseph Pharmacy", "Peoples Pharmacy", "Rex Pharmacy",
                "Lake Shore Pharmacy/Lake Pharmacy", "MyPharmacy", "White Horse Pharmacy", "Greenfield Pharmacy",
                "Morris Park Pharmacy/Yahia Aldailam", "Vanugaurd Pharmacy", "Prospect Care", "Burlington Pharmacy",
                "Clinton Pharmacy", "Crescent Pharmacy", "Ultracare Pharmacy", "Iqra Pharmacy", "Twin Parks Pharmacy",
                "Main St. Pharmacy", "Elixirx Apothecary", "Broad Specialty Pharmacy", "Professional Center Pharmacy",
                "NostrumRX Pharmacy", "Broadway Health Pharmacy", "Penlar Pharmacy", "Mt. Prospect Pharmacy",
                "Good RX/Hasibullah Mir", "FamilyCare NJ/Family Care Pharmacy", "Grace Pharmacy", "Sante Integrative Pharmacy", "Vcare RX",
                "Bestchoice RX", "Health Plus", "NYS Pharmacy", "Lifeline Baltimore Pharmacy", "Medics Pharmacy",
                "psp/komal bajwa", "International Pharmacy", "Emmaus Drug Store", "White Plains Pharmacy", 
                "Hub Specialty Pharmacy", "West Hartford Apothecary", "City Meds", "Ramtown Pharmacy", 
                "Albini Pharmacy", "Modern Pharmacy", "Shorham Drugs", "Quality Pharmacy", "Admin Medlife", 
                "ReadyRx Pharmacy", "Star Care Pharmacy", "FamilyCare NY/Family Care/family care specialty pharmacy", 
                "Tammy Care", "Skylands Family Pharmacy", "Bristol Pharmacy", "Milbrook Pharmacy", "Asbell Pharmacy", "A RST Rome Pharmacy",
                "Apex Health Pharmacy", "Firo Pharmacy", "Rockaway Drug Rx Pharmacy", "Star Pharmacy", "Eagle Rock"
            ]

            prescribers = [
                "makar, gamil", "majid, saniea", "dresdner, michael", "denoble, shaghayegh", "hainer, meg", "barness, michael", "mazzoccoli, vito",
                "saitta, jacqueline", "zhang, yuqing" , "shen, angela", "zhou, jin", "cao, ning", "chan, sing" , "khan, saima", "fox, alissa b.",
                "ferrara, elizabeth", "mian, bilal", "rivas, jimena", "calderon, rosa", "onyeador o., beatrice", "revoredo, fred", "marani dicovski, marcela",
                "agarwala, ajay", "shah, sulay", "fowler, emilie", "nizam, mohammed", "powell, michelle", "vukic, mario", "rojas, milagros",
                "jafri, syed", "ali, shaik", "wilson-tarpeh, ellen", "brown, dwayne", "schlakman, brandon", "friedberg, andrea", "mellul, david",
                "weinstock, brett", "rosenfeld, deborah", "wuzzardo, brandon", "florio suskevic, katherine", "mcnally, kristie", "patel, pradip", 
                "pintauro, kellyann", "parikh, haley", "tran, jacques","yu, may", "cruz, taisha", "pintauro, robert", "som, sumit", "humera, rafath",
                "szymanek, erica", "khan, intazam", "moeller, chaim", "ilyayeva, stella", "izrayelit, leonid", "fashakin, emmanuel", "mannan, bilal",
                "bognet, joseph", "westgate, danielle", "romascavage, frank", "kaufman, kathy", "swartz, stephen", "mazzocchi, dominic",
                "van der sluis, ralf", "movva, srinivasa", "bozzi, meredith", "demarco, lauren", "bijal, dave", "maykish, susan", "khesin, yevgeniy", 
                "alemu, ermiyas", "chi, danny", "morgan, dorcas", "belman, anna", "enuma, celestina", "cervone, joseph", "kochhar, rikhil", 
                "lira, lorraine", "vitale, joseph", "fellus, jonathan", "rapadas, cathryn", "haghverdi, mojdeh", "marquinez, anthony", 
                "cadesky, adam", "kapoor, anil", "pildysh, inna", "siddiqui, anila", "sammartino, robert", "jing, tong", "hitchner, allison", 
                "hyun, jae", "tan, wu", "peters, dana", "solaimanzadeh, sima", "noor, emad", "leone, matthew", "mikolaenko, ivan", "saw, thazin", 
                "antebi, yael", "korogluyev, mikhail", "kremen, inna", "gupta, manjari", "owunna, uzoma", "gross, renee", "gleason, abigail", "brown, jennifer",
                "tung, william", "nieves, jessica", "schuler, anna", "hussaini, batool", "escobar, paola", "frenkel, violina", "shahid, haroon"
            ]

            rows = max(len(pharmacies), len(prescribers))

            def get_column_label(index):
                label = ""
                while index >= 0:
                    label = chr(97 + (index % 26)) + label  
                    index = (index // 26) - 1
                return label

            print(' ======================= PHARMACIES ======================= | ======================= PRESCRIBERS ======================= ')

            for i in range(rows):
                pharmacy = f"{i + 1}. {pharmacies[i]}" if i < len(pharmacies) else ""  
                
                if i < len(prescribers):
                    label = f"{get_column_label(i)}.".ljust(4)  # Make label fixed width
                    name = prescribers[i]
                    prescriber = f"{label} {name}"
                else:
                    prescriber = ""

                print(f"{pharmacy.ljust(50)} {' ' * 13} | {prescriber}")

            number_inp = input(f'\n\nEnter number you want to open the pharmacy CMM...')
            if number_inp.isdigit():
                selected_pharmacy = pharma_mapping.get(number_inp)

                if selected_pharmacy in self.pharma_data:
                    cmm_usernmae = self.pharma_data[selected_pharmacy][0]
                    cmm_pass = self.pharma_data[selected_pharmacy][1]
                    gmail_username = self.pharma_data[selected_pharmacy][2]
                    gmail_pass = self.pharma_data[selected_pharmacy][3]
                    fax_no = self.pharma_data[selected_pharmacy][5]
                    sender_email = self.pharma_data[selected_pharmacy][6]
                    webhook_url = self.pharma_data[selected_pharmacy][7]
                    mailbox_email = self.pharma_data[selected_pharmacy][8]
                    mailbox_pass = self.pharma_data[selected_pharmacy][9]
                    aliases = self.pharma_data[selected_pharmacy][10]
                    zip_code = self.pharma_data[selected_pharmacy][11]
                    session_id = self.pharma_data[selected_pharmacy][12]
                else:
                    print(f'No option as: {number_inp}')
                    continue
            else:
                selected_prescriber = presc_mapping.get(number_inp)
                if selected_prescriber in self.pres_data:
                    cmm_usernmae = self.pres_data[selected_prescriber][0]
                    cmm_pass = self.pres_data[selected_prescriber][1]
                    gmail_username = self.pres_data[selected_prescriber][2]
                    gmail_pass = self.pres_data[selected_prescriber][3]
                    fax_no = self.pres_data[selected_prescriber][5]
                    sender_email = self.pres_data[selected_prescriber][6]
                    webhook_url = self.pres_data[selected_prescriber][7]
                    mailbox_email = self.pres_data[selected_prescriber][8]
                    mailbox_pass = self.pres_data[selected_prescriber][9]
                    aliases = self.pres_data[selected_prescriber][10]
                    zip_code = self.pres_data[selected_prescriber][11]
                    session_id = self.pres_data[selected_prescriber][12]
                else:
                    print(f'No option as: {number_inp}')
                    continue

                
            # if zip_code:
            print(f'Zip Code Checker --------------------- {zip_code}')

            proxy_url = f'https://{self.proxy_username}__cr.us;zip.{zip_code};sessid.{session_id};sessttl.60:{self.proxy_password}@{self.proxy_address}:{self.proxy_port}'

            seleniumwire_options = {
                'proxy': {
                    'http': proxy_url,
                    'https': proxy_url,
                }
            }

            options = Options()

            driver = swebdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options,
                seleniumwire_options=seleniumwire_options
            )
            #     # driver.get('https://www.showmyip.com/')
                # input('Check Your IP.....')

                
            # else:
            #     print(f'Zip Code --------------------- {zip_code}')
                # input('Open Your VPN.....')

            # options = Options()
            # driver = webdriver.Chrome(options=options)

            login_status = self.CMM_login(driver)
            if login_status['status'] == 'success':
                # input('enter...')
                time.sleep(25)
                if sender_email:
                    fetch_otp_status = self.fetch_otp_outlook()
                elif gmail_username:
                    fetch_otp_status = self.fetch_otp_gmail()
                elif mailbox_email:
                    fetch_otp_status = self.fetch_otp_mailbox()
                if fetch_otp_status:
                    if fetch_otp_status['status'] == 'success': 
                        otp_result = fetch_otp_status['data']
                        otp_field = driver.find_element(By.ID, "input45")
                        otp_field.send_keys(otp_result)

                        verify_btn = driver.find_element(By.CSS_SELECTOR, ".button.button-primary")
                        verify_btn.click()
                        print(f'FAX NUMBER --------------------- {fax_no}')

                        time.sleep(5)
                        invalid_code = driver.find_elements(By.XPATH, '//*[@id="input-container-error60"]')
                        if invalid_code:
                            print('Code fetched is invalid..Input code manually..')
                            input('Press Enter if code done and verified...')
                    else:
                        print('Unable to fetch code..Input code manually..')
                        input('Press Enter if code done and verified...')
                else:
                    print('Unable to fetch code..Input code manually..')
                    input('Press Enter if code done and verified...')

                usi_check = True
                while usi_check:
                    usi_inp = input('Press y or Y to Switch to Other CMM...')
                    if usi_inp in ('y','Y'):
                        driver.quit()
                        usi_check = False
                    else:
                        print('Enter y or Y only...')

    
if __name__ == "__main__":
    c1 = CoverMyMedsAutomate()
    c1.main()
