from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import sys
import html
class fuzzer:

    def read_charts_file(self,c_file):
        """Read chars file"""
        chars = []
        if c_file == "chars.txt":
            with open(c_file) as file:
                for line in file:
                    if not line == "":
                        chars.append(line)

        return chars
    def read_vector_file(self,v_file):
        """Read vector file"""
        vectors = []
        if v_file =="vectors.txt":
            with open(v_file) as file:
                for line in file:
                    if not line == "":
                        vectors.append(line)

        return vectors

    def read_sensitive_file(self,s_file):
        """read sensitive file"""
        sensitive = []
        if s_file == "sensitive.txt":
            with open(s_file) as file:
                for line in file:
                    if not line == "":
                        sensitive.append(line)
        return sensitive

    def guess_combination(self,w_file,ext_file):
        """Compute all combination of the word and extension"""
        words = []
        extensions = []
        combinations = []

        """if extension file is not given then use default extension php"""
        if not w_file == "":
            if ext_file =="":
                with open(w_file, 'r') as file:
                    for word in file:
                        combinations.append(word.strip()+".php")

            else:
                with open(w_file, 'r') as file:
                    for word in file:
                        words.append(word.strip())
                with open(ext_file,'r') as file:
                    for extension in file:
                        extensions.append(extension.strip())

                for word in words:
                    combin = ""
                    combinations.append(word)
                    for extension in extensions:
                        combin = word+"."+extension
                        combinations.append(combin)

        return combinations

    def page_guessing(self,url,session,words,extension):
        """page guessing for using the return list from guess combination"""
        guessing_list = self.guess_combination(words,extension)
        result = []
        if not url[-1] == '/':
            url +='/'
        guess_link = ""
        for i in guessing_list:

            guess_link += url + i
            res = session.get(guess_link)

            if res.status_code == 200:
                result.append(guess_link)

            guess_link = ""

        return result

    def page_discovery(self, target_link,session,base_url):
        """Crawling every possible links or pages from target_link list"""
        result = []
        domain = self.get_domain(base_url)
        for link in target_link:
            result.append(link)
        for url in target_link:

            res = session.get(url)
            soup = BeautifulSoup(res.content,"html.parser")

            link_list = soup.findAll('a',href = True)

            for link in link_list:
                link = str(link['href'])
                if link.startswith(domain):
                        result.append(link)

                if not link.startswith("http"):
                    if link.startswith("/") and link.endswith("/"):
                        final_path = urljoin(url,link)
                        if self.is_valid(session, final_path):

                            if not final_path in result:
                                result.append(final_path)
                        else:
                            final_path = self.reconstruct_falsed_url(url, link)
                            result.append(final_path)
                    elif link.endswith("/"):

                        final_path = urljoin(url+"/",link)
                        if self.is_valid(session,final_path):

                            if not final_path in result:
                                result.append(final_path)
                        else:
                            final_path = self.reconstruct_falsed_url(url,link)
                            result.append(final_path)
                    else:

                        final_path = urljoin(url , link)
                        if self.is_valid(session,final_path):

                            if not final_path in result:
                                result.append(final_path)
                        else:
                            final_path = self.reconstruct_falsed_url(url, link)
                            result.append(final_path)



        return result

    def get_domain(self,url):
        domain = ""
        counter =0
        if not url[-1]=="/":
            url += "/"
        for i in range(len(url)):
            if url[i]=="/":
                counter +=1
                if counter ==3:
                    domain = str(url)[:i]
        return domain


    def input_discovery(self,found_link,session):
        """
        Fin all possible input from pages
        :param found_link:
        :param session:
        :return: not_available,data,cookies
        """
        not_available  = []
        data = []
        cookies = []
        available = []
        for link in found_link:
            try:
                res = session.get(link)
                soup = BeautifulSoup(res.content,'html.parser')
                form_list = soup.findAll('form')
                soup = BeautifulSoup(str(form_list),'html.parser')
                #form = soup.find('form')
                input_form_list = soup.findAll('input')
                if len(input_form_list)>0:
                    for input in input_form_list:
                        if "name=" in str(input) and "type=" in str(input) and "value=" in str(input):
                            input = str(input).replace("<","")
                            input = input.replace("/>", "")
                            data.append({link:input})
                            if link not in available:
                                available.append(link)
                            if session.cookies  not in cookies:
                                cookies.append(session.cookies)
            except:
                not_available.append(link)
        return available,not_available,data,cookies

    def parse_input(self,session,url):
        """Currently don't know how to test this, have not yet see a example of this"""
        res = session.get(url)
        result = []
        if res.status_code ==200:
            url_comp = str(url).split("/")
            for comp in url_comp:
                if "=" in comp:
                    input = comp.split("=")
                    to_page = input[1]
                    result.append(to_page)

        return result


    def authenticate(self,auth,url,session):
        if not url[-1] =="/":
            url+="/"


        """change security level to low"""
        if (auth == "dvwa"):
            if "fuzzer-tests" in url:
                url = url.replace("fuzzer-tests/", "") + "setup.php"
            url += "setup.php"
            """Submit create/reset database"""
            session.post(url, data={'create_db': 'Create / Reset Database'})
            """login"""
            url = url.replace("setup.php","")+ "login.php"
            resp = session.get(url)
            parsed_html = BeautifulSoup(resp.content, features="html.parser")
            input_value = parsed_html.body.find('input', attrs={'name': 'user_token'}).get("value")
            data_dict = {"username": "admin", "password": "password", "Login": "Login", "user_token": input_value}
            response = session.post(url, data_dict)

            """change security level"""
            url = str(url).replace('login.php', 'security.php')
            resp = session.get(url)
            parsed_html = BeautifulSoup(resp.content, features="html.parser")
            input_value = parsed_html.body.find('input', attrs={'name': 'user_token'}).get("value")
            session.post(url, data={'security': 'low', 'seclev_submit': 'Submit', 'user_token': input_value})

    def reconstruct_falsed_url(self,abs_url,re_url):
        """reconstruct url if constructed url by using urljoin does not work properly"""
        return abs_url+"/"+re_url


    def is_valid(self,session,cur_url):
        """Check if a url is valid"""
        res = session.get(cur_url)

        if res.status_code == 404:
            return False
        return True

    def test_sanitization_vector(self,session,urls,vectors,sensitive,allow_time,chars):

        """Default vectors """

        if vectors ==[] and chars == []:
            vectors=["<",">"]
        elif not vectors ==[] and not chars == []:
            vectors.extend(chars)
        elif vectors==[] and not chars ==[]:
            vectors = chars

        if allow_time == 0:
            """If time is not given then set to default time 5"""
            allow_time = 5

        sens = []
        leak = []
        broken = []
        time_out = []
        try:
            for vector in vectors:
                payload = dict()
                for base in urls:
                    if vector != html.escape(vector, quote=False):
                        r = session.get(base,timeout = allow_time)
                        soup = BeautifulSoup(r.content, 'html.parser')
                        form_list = soup.findAll('form')
                        soup = BeautifulSoup(str(form_list), 'html.parser')
                        input_field = soup.findAll('input')
                        

                        if len(input_field) > 0:
                            for input in input_field:
                                value = vector
                                if "type" in input and input["type"] in ("submit", "hidden"):
                                    value = input["value"]
                                if "name=" in str(input) and "type=" in str(input) and "value=" in str(input):
                                    payload[input["name"]] = value
                                r = session.post(base, data=payload,timeout=allow_time)
                                if r.status_code ==200:
                                    response_content_casefold = r.text.casefold()
                                    if vector in r.text:
                                        sens.append(vector)
                                    if len(sensitive)>0:
                                        for word in sensitive:
                                            if word.casefold() in response_content_casefold:
                                                leak.append(word)
                                else:
                                    broken.append(base)
            # Catch the timeout exception only
        except requests.exceptions.Timeout:
            print("time out")
            time_out.append(base)
        return sens, leak, broken,time_out
    def fuzzer(self,input,session):
        command = ""
        extension_file=""
        words_file = ""
        custom_auth=""
        vector_file = ""
        sensitive_file = ""
        chars_file=""
        time = 0
        url = ""

        try:
            for option in input:
                option = str(option)
                if "http" in option:
                    url = option
                if "--custom-auth" in option:
                    custom_auth = str(option).split("=")[1]
                elif "--common-words" in option:
                    words_file = str(option).split("=")[1]
                elif "--extensions" in option:
                    extension_file = str(option).split("=")[1]
                elif "discover" in option:
                    command = "discover"
                elif "test" in option:
                    command ="test"
                elif "--sanitized" in option:
                    chars_file = str(option).split("=")[1]
                elif "--vectors" in option:
                   vector_file = str(option).split("=")[1]

                elif "--slow" in option:
                    time = int(str(option).split("=")[1])

                elif "--sensitive" in option:
                    sensitive_file = str(option).split("=")[1]



            if custom_auth == "dvwa":

                self.authenticate(custom_auth, url,session)
            if command == "discover":

                print("Start guessing pages:\n")
                for combin in self.guess_combination(words_file,extension_file):
                    print("\tGuessing link: " + combin)
                print("\n")
                print("------------------------------------------------")


                print("Page guessed:\n")
                target_link = self.page_guessing(url,session,words_file,extension_file)
                for link in target_link:
                    print("\t"+link)
                print("\n")
                print("------------------------------------------------")

                found_links = self.page_discovery(target_link,session,url)
                found_links.extend(target_link)
                print("Link discovered:\n")
                for link in found_links:
                    print("\t"+link)
                print("\n")
                print("------------------------------------------------")

                available,nodata,data,cookies = self.input_discovery(found_links,session)
                print("No input field found on following links:\n")
                for link in nodata:
                    print("\t"+link)
                print("------------------------------------------------")
                print("Input field found on following links:")
                for link in data:
                    for key in link.keys():
                        print("\t"+key)
                        print("\t"+link.get(key))
                        print("\n")
                print("------------------------------------------------")
                print("Cookies input: \n")
                for i in cookies:
                    print("\t"+str(i))
                    print("\n")

            elif command == "test":
                print("Start guessing pages:\n")
                for combin in self.guess_combination(words_file, extension_file):
                    print("\tGuessing link: " + combin)
                print("\n")
                print("------------------------------------------------")

                print("Page guessed:\n")
                target_link = self.page_guessing(url, session, words_file, extension_file)
                for link in target_link:
                    print("\t" + link)
                print("\n")
                print("------------------------------------------------")

                found_links = self.page_discovery(target_link, session, url)
                found_links.extend(target_link)
                print("Link discovered:\n")
                for link in found_links:
                    print("\t" + link)
                print("\n")
                print("------------------------------------------------")

                available, nodata, data, cookies = self.input_discovery(found_links, session)
                print("No input field found on following links:\n")
                for link in nodata:
                    print("\t" + link)
                print("------------------------------------------------")
                print("Input field found on following links:")
                for link in data:
                    for key in link.keys():
                        print("\t" + key)
                        print("\t" + link.get(key))
                        print("\n")
                print("------------------------------------------------")
                print("Cookies input: \n")
                for i in cookies:
                    print("\t" + str(i))
                    print("\n")

                print("------------------------------------------------")
                print("Test for santization")
                print("This process may take a while due to large data set....")

                vectors = self.read_vector_file(vector_file)
                sensitive = self.read_sensitive_file(sensitive_file)
                chars = self.read_charts_file(chars_file)
                sens, leak, broken, time_out = self.test_sanitization_vector(session, available, vectors, sensitive,
                                                                             time, chars)
                print("\tFound Unsanitized inputs: " + str(len(sens)))
                print("\tFound leaked data: " + str(len(leak)))
                print("\tFound broken link: " + str(len(broken)))
                if len(broken) > 0:
                    for i in broken:
                        print("\t" + i)
                print("\tFound potential DOS vulnerabilities: " + str(len(time_out)))


        except IndexError:
            print("Unrecongnized command")



def main():
    fuzz = fuzzer()
    session = requests.session()
    fuzz.fuzzer(sys.argv,session)

if __name__ == '__main__':
    main()