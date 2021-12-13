# Causality of Public Opinions

Granger causality test for the posts in social networks 

![](https://img.shields.io/badge/language-zh--CN-orange)
![](https://img.shields.io/badge/dependencies-Python%203.9-blue)
![](https://img.shields.io/badge/dependencies-Django%204.0-green)
![](https://img.shields.io/badge/dependencies-TensorFlow%202.6-orange)

Chinese documentation: more details in 
[documentation](./doc/舆情事件的Granger因果检验软件-说明书.docx)

## Introduction

A discussion will be raised when an enterprise, organization of famous
individual announces an activity. However, their competitors (especially
bad ones) will hire a lot of robots and zombie accounts to publish
negative opinions in social networks. This phenomenon will drive normal
individuals away from the truth.

This software can:
1. Find obvious events against the noisy and unordered opinions.
2. Test the causality between highly active accounts, to figure out how one
is affected by other's opinions or affects others.

The software use BERT-3 model to extract features from text, and use DBSCAN
algorithm to cluster posts into several events. Finally, it uses Granger
causality test to figure out the causality between different accounts.

As a conclusion, this technology is designed to help distinguish real public 
opinion from intended intensive promotion.

## Citation

BERT-3 Preprocessing (Chinese Language): 
https://tfhub.dev/tensorflow/bert_zh_preprocess/3

BERT-3 Model (Chinese Language): 
https://tfhub.dev/tensorflow/bert_zh_L-12_H-768_A-12/3

Data collection tool: https://github.com/dataabc/weibo-search


## Installation

The current folder of command line is the software's project root.

### 1. Token

Create a `token/` in project root, and include the following files in it.

(1) `django_secret_key`

There should be a string about 52 characters, being a secret key for 
communication between client and web server. The string can be generated in
[Djecrety](https://djecrety.ir/) website.

(2) `smtp.json`

If you don't use a registration confirming service by email, `smtp.json` is 
not necessary. At the same time, you should disable registry related links in
`sina_event_chain_django_cn/urls.py`.

There should be the config of web maintainer's email sender in this file. 
The format is:

```json
{
  "host": "example.com",
  "port": 465,
  "username": "registration@example.com",
  "password": "anypassword"
}
```

### 2. Python environment

Install required Python packages:

```
pip install -r requirements.txt
```

It is a maximum required package. With the environment, all functions can be 
used, but not all functions are necessary.

Navigate to the project folder, and create the database and superuser:

```
python manage.py migrate
python manage.py createsuperuser
```

Follow the instructions in the command line. This user has the highest 
permission in this software.

### 3. Administrator's settings

Run the command: 

```
python manage.py 0.0.0.0:$port --insecure
```

The IP address can only be 127.0.0.1 (for local use only) or 0.0.0.0 (for web 
server), and `port` can be customized. After that, the website will be running
at `https://example.com:$port/main`.

(1) Registry permission

1. Visit `https://example.com:$port/admin`. 
2. Create at least one group instance, for example, named "Free plan" and
   users can freely register into.
3. Create a register group instance, and link to "Free plan".
4. Add proper permissions to "Free plan", at least including:
   "add, change, view Register", "add, delete, change, view Task", 
   "add, delete, change, view AsyncErrorMessage", and
   "add, delete, change, view Column".
