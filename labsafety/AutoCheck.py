# -*- coding: utf-8 -*-
# @Time      :2022/9/22 14:56
# @Author    :ym
# @Description: 安全教育学习视频自动提交

import requests
import json


class AutoCheck(object):

    def __init__(self):
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json;charset=UTF-8",
            # 这里填你们的token
            "Authorization": "Bearer ead8347a-ef32-4f94-9401-a30ba3bd5969",
            # "Authorization": "",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",

        }
        if self.headers["Authorization"] == "":
            print("请填写token")
            exit(0)
        self.repeat = False

    def get_page_list(self, pageNum=0, pageSize=10):
        """
        总共87页
        获取页面列表,返回所有的ID列表，然后自动完成
        :param pageNum:
        :param pageSize:
        :return: id的一个列表 []
        """
        pass
        url = "https://labsafety.gdut.edu.cn/chem/api/exam/learningStudy/my?pageNum=" + str(
            pageNum) + "&pageSize=" + str(pageSize)
        data = {
            "collegeId": "null",
            "isDelete": 0,
            "level": "null",
            "pageNum": pageNum,
            "pageSize": pageSize,
            # "pages": 0,
            # "size": 0,
            "title": "",
            "total": "87",
            "type": "null"
        }
        response = requests.post(url, headers=self.headers, timeout=10, data=json.dumps(data))
        # print(response.json())
        if response.status_code == 200:
            data = response.json()
            if data["status"] == 200:
                article_list = data["data"]["records"]
                ret_list = []
                for i in article_list:
                    ret_list.append(i["id"])

                return ret_list
            else:
                print("获取列表失败")
                return None

    def finish(self, id):
        """
        完成
        :param id:
        :return:
        """
        url = "https://labsafety.gdut.edu.cn/chem/api/exam/learningStudy/finishLearning/" + str(id)
        data = {
            "id": id
        }
        response = requests.post(url, headers=self.headers, timeout=10, data=json.dumps(data))
        print(response.json())
        if response.status_code == 200:
            data = response.json()
            if data["status"] == 200:
                print(str(id) + ":" + str(data["data"]))
                return True
            elif data["status"] == 50207:
                message = data["message"]
                # 出现学习时长不够情况，忽略，一段时间后再重复提交
                if message == '学习时长不满足，请学习完再确认。':
                    print("学习时长不够，请稍后再试")
                elif message == '请不要重复确认':
                    print(str(id) + ":" + "出现重复完成，自动结束学习脚本！")
                    self.repeat = True
                return False

    def get_page_detail(self, id):
        """
        获得页面详细信息，例如video等地址
        :param id:
        :return:
        """
        url = "https://labsafety.gdut.edu.cn/chem/api/exam/learningStudy/do/" + str(id)
        response = requests.post(url, headers=self.headers, timeout=10)
        print(response.json())
        if response.status_code == 200:
            data = response.json()
            if data["status"] == 200:
                print(str(id) + ":" + str(data["data"]))
                return True
            else:
                print(str(id) + ":" + "获取详情失败")
                return False

    def list_finish(self, round=1):
        """
        完成本页视频
        :param id_list:
        :return:
        """
        id_list = self.get_page_list(round)
        for i in id_list:
            self.get_page_detail(i)
            self.finish(i)
            if self.repeat:
                return False
        return True


if __name__ == "__main__":
    """
    ps: 
        1.获得的列表是从未完成开始的，已经完成的会在后面出现，出现重复确认脚本会自动跳过剩下的任务
        2.视频是后台计算完成情况，具体怎么计算不知道。反正先跑一遍，然后挂在那里等一会重新跑一遍就行
        3.可能是根据视频获取时间开始算？有点蠢啊，
    """
    i = 1
    while i <= 8:
        repeat = AutoCheck().list_finish(i)
        print("_____________________________________")
        print("第" + str(i) + "页完成")
        i = i + 1
        if not repeat:
            print("出现重复code,自动结束")
            break
