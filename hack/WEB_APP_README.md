# enhanced code analyzer web application

a full-stack web application for analyzing python codebases with energy metrics, ai insights, and advanced dead code detection.

## features

### 🎯 core functionality
- **file upload**: drag & drop python files for analysis
- **dead code detection**: identify unused functions and code blocks
- **energy tracking**: measure and estimate energy consumption
- **ai-powered insights**: gpt integration for intelligent code analysis
- **async/threading detection**: identify concurrent code patterns

### 🎨 modern ui
- **react frontend**: responsive, modern interface with tailwind css
- **real-time analysis**: instant feedback on code analysis
- **diff viewer**: visualize suggested code changes
- **file management**: upload, analyze, and manage multiple files

### 🔧 advanced features
- **safe code removal**: generate cleaned versions of files
- **code optimization**: ai-powered code rewriting for efficiency
- **energy metrics**: co2 emissions tracking and reporting
- **api documentation**: auto-generated fastapi docs

## architecture

```
enhanced code analyzer web app
├── backend/                 # fastapi server
│   └── main.py             # api endpoints and logic
├── frontend/               # react application
│   ├── src/
│   │   ├── App.js          # main application component
│   │   ├── index.js        # app entry point
│   │   └── index.css       # tailwind styles
│   ├── package.json        # react dependencies
│   └── tailwind.config.js  # tailwind configuration
├── enhanced_analyzer.py    # core analysis engine
├── start_web_app.py        # startup script
└── requirements.txt        # python dependencies
```

## quick start

### 1. install dependencies

```bash
# install python dependencies
pip install -r requirements.txt

# install node.js dependencies (if you have node.js installed)
cd frontend
npm install
cd ..
```

### 2. start the application

```bash
# run the startup script (recommended)
python start_web_app.py

# or start manually:
# terminal 1 - backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# terminal 2 - frontend
cd frontend
npm start
```

### 3. access the application

- **frontend**: http://localhost:3000
- **backend api**: http://localhost:8000
- **api docs**: http://localhost:8000/docs

## usage

### uploading files
1. drag and drop python files onto the upload area
2. or click to select files from your file system
3. files are automatically uploaded to the backend

### analyzing code
1. select an uploaded file from the file list
2. configure analysis options:
   - **openai api key**: for ai-powered insights
   - **track energy**: measure energy consumption
   - **show diff**: generate code diff for suggested changes
   - **safe remove**: create cleaned version of file
   - **rewrite inefficient**: ai-powered code optimization
3. click "analyze file" to start analysis

### viewing results
- **function analysis**: see detailed breakdown of each function
- **dead code detection**: identify unused functions
- **energy impact**: view energy consumption metrics
- **ai insights**: get explanations and suggestions
- **code diff**: visualize suggested deletions
- **optimized code**: view ai-rewritten versions

## api endpoints

### file management
- `POST /upload` - upload python file
- `GET /files` - list uploaded files
- `DELETE /files/{file_id}` - delete uploaded file

### analysis
- `POST /analyze/{file_id}` - analyze uploaded file with options

### parameters
- `openai_key` (string): openai api key for ai analysis
- `track_energy` (boolean): enable energy tracking
- `show_diff` (boolean): generate code diff
- `safe_remove` (boolean): create cleaned file
- `rewrite_inefficient` (boolean): ai code optimization

## development

### backend development
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### frontend development
```bash
cd frontend
npm start
```

### adding new features
1. **backend**: add new endpoints in `backend/main.py`
2. **frontend**: add new components in `frontend/src/`
3. **analysis**: extend `enhanced_analyzer.py` with new detection logic

## deployment

### production setup
1. build the frontend:
   ```bash
   cd frontend
   npm run build
   ```

2. serve with a production server:
   ```bash
   # using nginx or similar
   # configure to serve frontend/build and proxy api calls to backend
   ```

3. run backend with production server:
   ```bash
   cd backend
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

### docker deployment
```dockerfile
# backend dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ ./backend/
COPY enhanced_analyzer.py .
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## troubleshooting

### common issues
1. **port conflicts**: change ports in startup script
2. **cors errors**: check cors configuration in backend
3. **file upload fails**: check file size limits and permissions
4. **analysis fails**: verify python dependencies are installed

### debugging
- check browser console for frontend errors
- check backend logs for api errors
- use fastapi docs at http://localhost:8000/docs for api testing

## contributing

this is an open-source project. contributions are welcome!

1. fork the repository
2. create a feature branch
3. make your changes
4. test thoroughly
5. submit a pull request

## license

mit license - feel free to use and modify for your projects. 