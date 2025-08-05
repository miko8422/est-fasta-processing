# est-fasta-processing
This is the repo for EST Client code. To use the client code, you need to setup EFI-EST project at your local machine and deploy the `server.py` code and config the network env.

To build the env for both server side and client side:

```
conda create -n est-inf python=3.10
conda activate est-inf
pip install -r requirements.txt
```

As the est project local deploy, I will write an complete instructions in the future.

```
Place Holder
```

To deploy the server, use commands as follows.

```
python server.py
```

To use the project, use commands as follows.

```
python client.py .\test.fasta --filter-min-val 25  --output-dir results --server http://your_hosted_server
```