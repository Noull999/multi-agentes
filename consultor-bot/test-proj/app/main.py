from fastapi import FastAPI

app = FastAPI(title='test-proj')

@app.get('/')
def root():
    return {'message': 'test-proj API'}
