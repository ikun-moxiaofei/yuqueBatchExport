import os
import re
import requests
import pdfkit

# todo 文件保存路径
DATA_PATH="D:\zhuomian\yuque\yuque_dome"
# todo 修改格式  0：MarkDown 1：html 2：pdf
DATA_TYPE=0

YUQUE_API="https://customspace.yuque.com/api/v2"
USER_AGENT="agent"
# todo 用户的Token 访问：https://www.yuque.com/settings/tokens，新建一个Token
USER_TOKEN="***********************************"
WKHTMLTOPDF_PATH=r"D:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"

class CExportYuQueDocs:
    def __init__(self):
        try:
            self.api = YUQUE_API
            self.headers = {
                "User-Agent": USER_AGENT,
                "X-Auth-Token": USER_TOKEN
            }
            self.data_path = DATA_PATH
            self.doc_type = DATA_TYPE
            self.pdfkit_config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
            self.pdfkit_options = {
                'page-height': '297',
                'page-width': '210',
                'encoding': 'UTF-8',
                'custom-header': [('Accept-Encoding', 'gzip')]
            }
        except:
            raise ValueError("Parameter Error!")

    def login(self):
        request = requests.get(url=self.api + '/user', headers=self.headers)
        if 200 != request.status_code:
            raise ValueError("Token Error!")
        userJson = request.json()
        self.login_id = userJson['data']['login']
        self.uid = userJson['data']['id']
        self.username = userJson['data']['name']
        print(f"{self.username} Login Success!")

    def getRepos(self):
        """get the user's repos"""
        reposRequest = requests.get(self.api + '/users/' + self.login_id + '/repos', headers=self.headers).json()
        reposList = []
        for item in reposRequest['data']:
            # rid=warehouse's is,
            reposList.append({"id": item['id'], "name": item['name']})
        return reposList

    def getDocs(self, reposList):
        listDocs = []
        for repos in reposList:
            docsRequest = requests.get(self.api + '/repos/' + str(repos['id']) + '/docs',
                                         headers=self.headers).json()
            for item in docsRequest['data']:
                listDocs.append(
                    {
                        "id": repos['id'],
                        "title": item['title'],
                        "description": item['description'],
                        "slug": item['slug'],
                        "name": repos["name"]
                    }
                )

        for item in listDocs:
            docDetails = requests.get(self.api + '/repos/' + str(item['id']) + '/docs/' + item['slug'],
                                            headers=self.headers).json()
            if 0 == self.doc_type:
                docDetails_1 = re.sub(r'\\n', "\n", docDetails['data']['body'])
                docsData = re.sub(r'<a name="(.*)"></a>', "", docDetails_1)
            else:
                docsData = re.sub(r'<!doctype html>', r'<!doctype html><head><link rel="stylesheet" href="http://editor.yuque.com/ne-editor/lake-content-v1.css"></head>',
                                  docDetails['data']['body_html'])

            yield docsData, item["name"], item['title']


    def saveDocs(self, data, name, title):
        if 0 == self.doc_type:
            saveFolder = f"{self.data_path}/md/{name}"
            filePath = saveFolder + f"/{title}.md"
        elif 1 == self.doc_type:
            saveFolder = f"{self.data_path}/html/{name}"
            filePath = saveFolder + f"/{title}.html"
        elif 2 == self.doc_type:
            saveFolder = f"{self.data_path}/pdf/{name}"
            filePath = saveFolder + f"/{title}.pdf"
        else:
            raise ValueError(f"Error Type to Save! Type[{self.doc_type}]")

        if not os.path.exists(saveFolder):
            os.makedirs(saveFolder)

        if os.path.exists(filePath):
            try:
                os.remove(filePath)
            except Exception as e:
                raise ValueError(f"File [{filePath}] is occupied!")

        try:
            if 2 == self.doc_type:
                pdfkit.from_string(data, filePath, configuration=self.pdfkit_config, options=self.pdfkit_options)
            else:
                with open(filePath, 'a', encoding="utf-8") as fp:
                    fp.writelines(data)
            print(f"Save [{filePath}] Success!")
        except Exception as e:
            print(f"Save [{filePath}] Failed!")

    def start(self):
        self.login()
        reposList = self.getRepos()
        for item in self.getDocs(reposList):
            self.saveDocs(item[0], item[1], item[2])


if __name__ == "__main__":
    yq = CExportYuQueDocs()
    yq.start()


