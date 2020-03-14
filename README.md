# fast-elm 
- fast-elm is an elm clone project.

# stack:
- python + fastapi + mongodb.

# relative project
- front end : vue2-elm port 8000
- admin end: vue2-manage port 8002
- back end: fast-elm port 9001

# user guide:
  - environment:
    - python 3.7
    - fastapi
    - mongodb 4
    - environment tool: poetry
  - run backend server: 
    - poetry install
    - poetry shell
    - ./fmrun.sh
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
