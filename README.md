## 1. Create license.env file

## 2. Setup config file

## 3. Run
```
docker run \
  --env-file "$(pwd)/license.env" \
  -v "$(pwd)/configs/hello-world.json:/home/config.json" \
  shadowtraffic/shadowtraffic:latest \
  --config /home/config.json \
  --sample 10 \
  --stdout
```

```
docker run \
  --env-file "$(pwd)/license.env" \
  -v "$(pwd)/configs/voided_no_llm.json:/home/config.json" \
  -v "$(pwd)/output:/data" \
  shadowtraffic/shadowtraffic:latest \
  --config /home/config.json
```


```
docker run \
  --env-file "$(pwd)/license.env" \
  -v "$(pwd)/configs/voided_no_llm.json:/home/config.json" \
  -v "$(pwd)/output:/data" \
  -v "$(pwd)/python:/home/python" \
  shadowtraffic/shadowtraffic:latest \
  --config /home/config.json
```