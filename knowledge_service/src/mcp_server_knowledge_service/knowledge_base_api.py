import requests
import os
import re
import time
import os

# 查询知识库QA对
# question是QA对key值
# account是工号
# token是工号的token，登录icenter后得到
# kbaseName知识库名称
# kbaseid知识库Id
def query_kbase(question, account, token, kbaseName = None, kbaseid = None, 
                tag_names = [], #标签
                vectorType = 'bge-large-zh-v1.5', 
                searchType = 'vector', # 匹配类型。默认：vector。其他：mix es
                matchNumber = 3, # 最大匹配条数
                relatedIndex = 0.5, # 相关度阈值
                searchWeight = 0.5,  #权重
                logger = None):
    workspace = 'workspace'
    url = "https://rdcloud.zte.com.cn/zte-studio-iaab-kbase/api/v1/retrieve"
    payload1 = {"relatedIndex" : relatedIndex, 
               "matchNumber" : matchNumber,
               "searchWeight":0.5,
               "searchType":"vector",
               "isRank":False,
               "vectorType" : vectorType,
               "type":"kbase",
               "kbaseid":kbaseid,
               "ids":[{"id" : kbaseid, "kbaseId" : kbaseid}],
               "kbaseName":kbaseName,
               "tagNames":tag_names,
                "kbase": {
                    "ids": [
                    {
                        "id": kbaseid,
                        "kbaseId": kbaseid
                    }]},
                "folder": {
                    "ids": []
                },
                "file": {
                    "ids": []
                },
                "question": question,
                "metadataDisplay": False,
                "richTextSwitch": True
               }
    headers = {
        "X-Tenant-Id": 'ZTE',
        "X-Emp-No": account,
        "X-Auth-Value": token,
        "X-Lang-Id": "zh_CN",
        "Content-Type": "application/json"
    }
    result = ''
    try:
        response = requests.post(url, headers=headers, json=payload1)
        logger.info(f'请求成功，状态码:{response.status_code}')
        if response.status_code == 200:
            return True, response.json() 
    except Exception as e:
        msg=f'获取知识库只是失败!\n {repr(e)}'
        logger.error(msg)
        return False, msg
  
def query_kbase_and_return_one(question, account, token, kbaseName = None, kbaseid = None, tag_names = [], logger = None):
    status, response = query_kbase(question, account, token, 
            kbaseName = kbaseName, 
            kbaseid = kbaseid,
            matchNumber = 1,
            tag_names = tag_names,
            searchType = 'mix',
            relatedIndex = 0.5,
            logger = logger)
    if not status:
        return status, response
    # 判断response是dict类型，且response['bo']存在
    if response and isinstance(response, dict) and 'bo' in response and response['bo']:
        value = response['bo'][0]  # 取第一个
        if 'supplement' in value:
            return True, value['supplement']
    return False, 'not correct response'





