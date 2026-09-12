"""仅启动独立旅行应用，不启动上游检索服务。"""
import argparse
import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    uvicorn.run("manyou.api:app", host=args.host, port=args.port)
