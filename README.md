# How to use

## Sync SDK
```
from any_parser_rt.any_parser_rt import AnyParserRT

ap_rt = AnyParserRT(api_key="...")

md_output, total_time = ap_rt.extract(file_path="./data/test.pdf")
```
Check [example](example/example.ipynb)

## Async SDK

```
from any_parser_rt.any_parser_rt import AnyParserRT

ap_rt = AnyParserRT(api_key="...")

file_id = ap_rt.async_extract(file_path="./data/test.pdf")

md = ap_rt.async_fetch(file_id=file_id)
```

Check [example](example/async_example.ipynb)