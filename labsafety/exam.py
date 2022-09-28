# -*- coding: utf-8 -*-
# @Time      :2022/9/28 09:54
# @Author    :Ymir
import requests
import json
from tqdm import trange


class Exam(object):
    """
    考试自动提交，大概流程
    1.获得题库，题库校验
    1.获得考试ID和时间
    2.获得题目题库检测
    4.100分
    """

    def __init__(self):
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
            "Accept-Encoding": "application/json",
            # token 手动填写，和AutoCheck.py一样
            "Authorization": "",
            "Content-Type": "application/json"
        }
        # 域名
        self.url = "https://labsafety.gdut.edu.cn"
        # 题库
        self.database = {}
        self.database_path = "./database/database.json"
        self.timeout = 60
        self.exam_content = None
        self.__check_database()
        self.start_id = None
        pass

    def __check_database(self):
        """
        检查数据是否存在,不存在先自动爬取题库
        :return:
        """
        try:
            with open(self.database_path, "r+", encoding="utf-8") as f:
                txt = json.loads(f.read())
                self.database = txt
                print("数据加载完成！一共" + str(len(self.database)) + "条数据")
        except Exception as e:
            print("未发现数据库信息，自动从网站爬取！")
            self.load_database()
        pass

    def load_database(self):
        """
        加载题库
        :return:
        """
        # 获得所有题目的分类
        class_ids = self.get_all_knowledge()
        self.database = {}
        for item in class_ids:
            total, _ = self.get_question_by_id_page_num(str(item))
            i = 1
            for i in trange(1, int(total) + 1):
                _, question = self.get_question_by_id_page_num(str(item), page_num=i)
                if self.database.get(question["title"]):
                    option = self.database.get(question["title"])["option"]
                    list(option).append(question["option"])
                else:
                    self.database[str(question["title"])] = question
            print("题目数量增加：" + str(total))
            with open(self.database_path, "w+", encoding='utf-8') as f:
                txt = json.dumps(self.database)
                f.write(txt)
        print("数据爬取完成" + str(len(self.database)))
        # print("题目载入成功!题目总数：" + )

    def get_exam_id(self):
        """
        获取考试ID
        :return:
        """
        url = self.url + "/chem/api/exam/test/doing"
        response = requests.get(url, headers=self.headers, timeout=self.timeout)
        try:
            if response.status_code == 200:
                text = response.json()
                temp_id = text["data"][0]["id"]
                print("考试临时ID：" + str(temp_id))
                url = self.url + "/chem/api/exam/test/new/" + str(temp_id)
                response = requests.post(url, headers=self.headers, timeout=self.timeout)
                if response.status_code == 200:
                    text = response.json()
                    print("考试获得ID：" + str(text["data"]["id"]))
                    return text["data"]["id"]

            else:
                print(response.json())
                print("获取考试ID失败")
                exit(-1)
                return None
        except Exception as e:
            print("获取考试ID失败")
            print(e)
            exit(-1)
            return None
        pass

    def get_exam_content(self, start_id):
        """
        获取考试内容
        :return:
        """
        url = self.url + "/chem/api/exam/test/start/" + str(start_id)
        response = requests.post(url, headers=self.headers, timeout=60)
        self.start_id = start_id
        try:
            if response.status_code == 200:
                data_json = response.json()
                self.exam_content = data_json["data"]
                print(data_json)
                return data_json["data"]
            else:
                print("获取考试内容失败")
                return None
        except Exception as e:
            print("获取考试内容失败")
            print(e)
            return None
        pass

    def submit_exam(self, is_sumbit=False):
        """
        提交考试
        :return:
        """
        if not self.exam_content:
            print("未获取到考试内容,自动退出！")
            exit(-1)
        answers = self.exam_content["answers"]
        submit_answers = {}
        for (name, item) in answers.items():
            # 依次答题,三个种类
            new_item = []
            for i in item:
                # 需要添加一个userAnwer属性
                title = i["title"]
                question = self.database[title]
                if not question:
                    print("未找到题目内容！")
                    continue
                else:
                    # 问题选项
                    q_options = i["options"]
                    # 题库答案
                    option = question["option"]
                    flag = False
                    user_answer = None
                    if int(i["type"]) == 1:
                        # 单选
                        for j in q_options:
                            for k in option:
                                if j["optionValue"] == k["optionValue"]:
                                    user_answer = j["id"]
                                    flag = True
                            if flag:
                                break
                        i["answer"] = user_answer
                    elif int(i["type"]) == 2:
                        # 多选
                        user_answer = []
                        temp_ans = ""
                        for j in q_options:
                            for k in option:
                                if j["optionValue"] == k["optionValue"]:
                                    user_answer.append(j["id"])
                                    temp_ans += j["id"] + ","
                        temp_ans = temp_ans[:-1]
                        i["answer"] = temp_ans
                    elif int(i["type"]) == 3:
                        # TF
                        user_answer = option[0]
                        i["answer"] = user_answer
                    i["userAnswer"] = user_answer
                    new_item.append(i)
            submit_answers[name] = new_item
        self.exam_content["answers"] = submit_answers
        # 防止转义出现unicode编码
        data = json.dumps(self.exam_content, ensure_ascii=False)
        print("答案匹配完成")
        print(data)
        if not is_sumbit:
            print("关闭自动提交答案，请在手动保存id:" + str(self.start_id))
            exit(0)
        url = self.url + "/chem/api/exam/test/submit"
        # 提交答案
        response = requests.post(url, headers=self.headers, data=json.dumps(self.exam_content), timeout=60)
        try:
            if response.status_code == 200:
                data_json = response.json()
                print("考试返回：")
                print(data_json)
                print("考试得分" + str(data_json["data"]["score"]))
                return data_json["data"]
            else:
                print("提交考试失败")
                return None
        except Exception as e:
            print("提交考试失败")
            print(e)
            return None
        # 	String

    def get_all_knowledge(self):
        """
        获取所有知识点
        :return:
        """
        url = self.url + "/chem/api/exam/learningQuestion/statByKnowledge?excludeOtherTeam=true"
        response = requests.get(url, headers=self.headers, timeout=self.timeout)
        try:
            if response.status_code == 200:
                text = json.loads(response.text)
                list = text["data"]
                ret_list = []
                print("—————————————————————查询题目分类开始—————————————————————————————")
                for item in list:
                    ret_list.append(item["knowledgeId"])
                    print(item["knowledgeId"], item["knowledge"])
                print("—————————————————————查询题目分类结束—————————————————————————————")
                return ret_list
        except Exception as e:
            print("获得所以类型题目失败！请重试")
            print(e)
            exit(-1)

    def get_all_question_by_knowledgeId(self, knowledgeId):
        """
        根据id获得所有的题目
        :return:
        """
        url = self.url + "/chem/api/exam/learningQuestion/view?knowledgeId=" + str(knowledgeId)
        response = requests.get(url, headers=self.headers, timeout=self.timeout)
        try:
            if response.status_code == 200:
                data_json = response.json()
                know_list = data_json["data"]
                question_ids = know_list["questionIds"]
                print(data_json)
        except Exception as e:
            pass
        pass

    def get_question_by_id_page_num(self, id, page_num=1):
        """
        根据id和页码获得题目和答案
        :param id:
        :param pageNum:
        :return:
        type 1： 单选题
        type 2: 多选题
        type 3: 判断题
        """
        url = self.url + "/chem/api/exam/learningQuestion/next?knowledgeId=" + str(id) + "&pageNum=" + str(page_num)
        response = requests.get(url, headers=self.headers, timeout=self.timeout)
        total = 0
        if response.status_code == 200:
            data_json = response.json()
            # 如果正在考试就会禁止查看题库
            data_json = data_json["data"]
            questions = data_json["questions"]
            total = questions['total']
            records = questions["records"]
            if len(records) < 1:
                print("题目查找失败：", str(id), str(page_num))
                return None
            records = records[0]
            quests = {
                "id": records["id"],
                "title": records["title"],
                "type": records["type"],
                "answer": records["answer"],
                "rightAnswer": records["rightAnswer"],
            }
            # 保存正确的选项
            options = []
            if int(records["type"]) == 1:
                re_options = records["options"]
                for item in re_options:
                    if str(item["id"]) == str(quests["rightAnswer"]):
                        options.append(item)
                        quests["option"] = options
                        return total, quests
            elif int(records['type']) == 2:
                # 多选
                ans = str(records["rightAnswer"]).split(",")
                for item in records["options"]:
                    if str(item["id"]) in ans:
                        options.append(item)
                quests["option"] = options
                return total, quests
            elif int(records['type'] == 3):
                # 判断题,直接对错
                options.append(quests["rightAnswer"])
                quests["option"] = options
                return total, quests


if __name__ == "__main__":
    exam = Exam()
    #  如果不存在题库，可以尝试自己运行题库
    # exam.load_database
    # -----------------开始考试，但是默认不会给你提交--------------
    id = exam.get_exam_id()
    exam.get_exam_content(id)
    exam.submit_exam()
    # ----------------开始考试，自动提交代码成绩-------------------
    # 不想管的话，直接把其他的地方注释，润这部分的代码就行
    # id = exam.get_exam_id()
    # exam.get_exam_content(id)
    # exam.submit_exam(True)
    # -----------------回到考试，并提交大难------------------------
    # 这个部分是给不想1s,直接给你提交的，可以直接运行这个部分，需要先润第一部分开始开始，然后拿到id，然后运行这个部分
    # 记得注释掉第一部分
    # 这里填第一部分程序输出的id
    # id = "xxx"
    # exam.get_exam_content(id)
    # exam.submit_exam(True)




