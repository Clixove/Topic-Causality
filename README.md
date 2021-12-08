# Causality of Public Opinions

Granger causality test for the posts in social networks 

![](https://img.shields.io/badge/language-zh--CN-orange)
![](https://img.shields.io/badge/dependencies-Python%203.9-blue)
![](https://img.shields.io/badge/dependencies-Django%203.2-green)
![](https://img.shields.io/badge/dependencies-TensorFlow%202.6-orange)

## Acknowledge

BERT-3 Preprocessing (Chinese Language): 
https://tfhub.dev/tensorflow/bert_zh_preprocess/3

BERT-3 Model (Chinese Language): 
https://tfhub.dev/tensorflow/bert_zh_L-12_H-768_A-12/3

Data collection tool: https://github.com/dataabc/weibo-search

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

## Installation

The current folder of command line is the software's project root.

### 1. Build token files

Create `token` folder at project root. There should be several files in this folder:
- In `token/django_secret_key`, there should be a string about 52 characters, being a secret key for communication between client and web server. 
- In `token/smtp.json`, there should be the config of web maintainer's email sender. The format is: 
```json
{
  "host": "example.com",
  "port": 465,
  "username": "registration@example.com",
  "password": "anypassword"
}
```
- In `token/paypal.json`, there should be paypal sandbox's clinet ID and secret. In formal release, please replace `SandboxEnvironment` in `__init__` function in `paypal/models.py > PaypalClient` class with `LiveEnvironment`, and use live's clinet ID and secret in `token/paypal.json`. The format is:
```json
{
  "client_id": "anypassword",
  "secret": "anypassword"
}
```

If you don't use a registration confirming service by email, `smtp.json` is not necessary. However, you should delete `add_register`, `send_confirm_email` functions and `RegisterSheet` class, and modify `add_user` function to link the result of `LoginForm` directly.

### 2.	Build Python environment

Install required Python packages:

```
pip install -r requirements.txt
```

It is a maximum required package. With the environment, all functions can be used, but not all functions are necessary.

Navigate to the project folder, and create the database and superuser:

```
python manage.py migrate
python manage.py createsuperuser
```

Follow the instructions in the command line. This user has the highest permission in this software.

### 3. Build static files

Replace `STATICFILES_DIRS = ['templates/static']` with `STATIC_ROOT = 'templates/static'` in `sina_event_chain_django_cn/settings.py`.

Run the command: 
```
python manage.py collectstatic
```

Replace `STATIC_ROOT = 'templates/static'` with `STATICFILES_DIRS = ['templates/static']` in `sina_event_chain_django_cn/settings.py`.

Replace `DEBUG = True` with `DEBUG = False` in `sina_event_chain_django_cn/settings.py`.

### 4. Administrator's settings

Run the command: 
```
python manage.py 0.0.0.0:$port --insecure
```
The IP address can only be 127.0.0.1 (for local use only) or 0.0.0.0 (for web server), and `port` can be customized.

Visit [https://example.com:$port/admin](). Create at least one group. Add the groups, which users can freely add into, to "Register groups" table. These groups each must include the following permissions:
- My login: add, change, view Register
- Task manager: add, delete, change, view Task; add, delete, change, view AsyncErrorMessage;
  add, delete, change, view Column.
