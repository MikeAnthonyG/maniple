# Dlib (Python API) - precompiled for Lambda

## Build

### Python 2.7

```
./build.sh 2.7
```

or

### Python 3.6

```
./build.sh 3.6
```

## Testing

### Python 2.7

```
./test.sh 2.7
```

### Python 3.6

```
./test.sh 3.6
```

## Shell (for debugging)

### Python 2.7

```
docker run -v$(pwd):/app -it --rm lambci/lambda:build-python2.7 bash
```

### Python 3.6

```
docker run -v$(pwd):/app -it --rm lambci/lambda:build-python3.6 bash
```
