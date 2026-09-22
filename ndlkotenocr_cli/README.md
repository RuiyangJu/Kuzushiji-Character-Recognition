# NDLKotenOCR
This is for reference only. Please refer to the [original GitHub repository](https://github.com/ndl-lab/ndlkotenocr_cli) for details.

## Environment
* Please use the `requirements.txt` provided here.
```
  pip install -r requirements.txt
```
## Download
```
  git clone https://github.com/ndl-lab/ndlkotenocr_cli
```
* Download the NDLKotenOCR pre-trained models [here](https://1drv.ms/f/c/56c255dd1bb9ae9e/IgA4O6N0oUNJT4BNZ_-Gd7SUAQk5CvaYOZTJE46t2AGCUl0?e=gZqHBD). You can also access it through the [original GitHub repository](https://github.com/ndl-lab/ndlkotenocr_cli).
* Put the pre-trained models as follows:
```
ndlocr_cli
  └── src 
      ├── ndl_kotenseki_layout/models/ndl_kotenseki_layout_ver3.pth
      └── text_kotenseki_recognition/model-ver2
```
## Run
* For calculating the inference speed, after cloning the repository, replace the cloned `main.py` with the `main.py` provided here.
```
  python main.py infer input_root output_dir
```

* You can use the following command to obtain the peak GPU memory usage. Note that this may slightly increase the inference latency due to the monitoring overhead.
```
  python main.py infer input_root output_dir --monitor_gpu
```

* `input_root` and `output_dir` are as follows:
```
  input_root/
    └── img
        ├── page01.jpg
        ├── page02.jpg
        ・・・
        └── page10.jpg
```
```
  output_dir/
    ├── input_root
    │   ├── txt
    │   │     ├── page01.txt
    │   │     ├── page02.txt
    │   │    ・・・
    │   │    
    │   └── json
    │         ├── page01.json
    │         ├── page02.json
    │        ・・・
    └── opt.json
```

## Evaluate
* Revise the names of outputs:
```
  python revise_name.py --input output_dir/txt
```
* Evaluate the performance (CER):
```
  python evaluate.py --gt_dir gt_folder --pred output_dir/txt --out_csv output
```
