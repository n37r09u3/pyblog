# pyblog

基于https://github.com/xuming/micolog 的改造python blog系统

改造如下

1 去除gae独立运行
2 使用python3

## run with wsgi server

```
pip install waitress
waitress-serve --port=8080 app:application
```