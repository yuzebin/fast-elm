# fast-elm 
- fast-elm is an node-elm clone project.

# stack:
- python + fastapi + mongodb.

# relative project
- back end project: fast-elm port 9001
- front-end: [vue2-elm](https://github.com/bailicangdu/vue2-elm) port 8000
- admin-end: [vue2-manage](https://github.com/bailicangdu/vue2-manage) port 8002
- refer project: [node-elm](https://github.com/bailicangdu/node-elm)

# user guide:
  - run backend server: 
    - cd fast-elm
    - environment
      - python 3.7
      - fastapi
      - mongodb 4
      - environment tool: poetry
    - poetry install
    - poetry shell
    - start mongodb port 27017
    - import data
    - ./fmrun.sh
    - server run at http://localhost:9001
  - run frontend project
    - cd vue2-elm
    - npm install
    - npm run dev
    - goto http://localhost:8000
  - run admin end project
    - cd vue2-manage
    - npm install
    - npm run dev
    - goto http://localhost:8002
  - origion api refer:
    - node-elm project


# fast-elm 
- fast-elm 是一个 node-elm 克隆项目。

# 技术栈：
- python + fastapi + mongodb.

# 相关项目：
- 本项目：后端接口: fast-elm 端口 9001
- 前端项目: [vue2-elm](https://github.com/bailicangdu/vue2-elm) 端口 8000
- 管理端项目: [vue2-manage](https://github.com/bailicangdu/vue2-manage) 端口 8002
- 参考项目：[node-elm](https://github.com/bailicangdu/node-elm)

# 使用指南:
  - 运行后端接口:
    - cd fast-elm
    - 环境要求
      - python 3.7
      - fastapi
      - mongodb 4
      - 环境工具: poetry
    - poetry install
    - poetry shell
    - 启动 mongodb 端口 27017
    - 导入数据
    - 运行服务
      - ./fmrun.sh
    - 服务接口地址
      - http://localhost:9001
  - 运行前端项目
    - cd vue2-elm
    - npm install
    - npm run dev
    - 访问地址
      - http://localhost:8000
  - 运行管理端
    - cd vue2-manage
    - npm install
    - npm run dev
    - 访问地址
      - http://localhost:8002
  - 原始api参考：
    - node-elm 项目



