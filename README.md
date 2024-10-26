# CIEN-LWEN: A Novel Dual-Network Framework for Accurate and Efficient Pig Liveweight Estimation

---
If you have suggestion or question, please contact: **dongximing@webmail.hzau.edu.cn**
## Installation

---
### Set up the python environment
```shell
conda create -n CIEN-LWEN python=3.7
conda activate CIEN-LWEN

pip install torch==1.8.1+cu111 torchvision==0.9.1+cu111 torchaudio==0.8.1 -f https://download.pytorch.org/whl/torch_stable.html
pip install -r requirements.txt
```
### Compile cuda extension
```shell
ROOT=/path/to/CIEN-LWEN
cd $ROOT/CIEN/network
git clone https://github.com/jinfagang/DCNv2_latest.git
git checkout fa9b2fd740ced2a22e0e7e913c3bf3934fd08098
python setup.py build develop
```
### Download the LISAP dataset
We provide a **large-scale** dataset, LISAP(Liveweight and Instance Segmentation Annotation of Pigs), which
can be download [here](https://pan.baidu.com/s/1CBIc5zbNm7GOMzO4ni5tQA?pwd=hzau). Organize it as `$ROOT/LISAP` in this project.

Note: There are total 39 pigs in `weight_data.csv`. In LISAP, we only annotated **No.27~39**, because others pigs were
kept in other pens(the installation height were a little different). And **No.40** means the indeterminate ID.

## Testing

---

### Testing with CIEN
1. The pretrained model is already put in `$ROOT/CIEN/data/Trained_CIEN.pth`.
2. Test:
```shell
cd $ROOT/CIEN
python test.py --config_file default_CIEN --with_nms True
```
3. Speed:
```shell
cd $ROOT/CIEN
python test.py --config_file default_CIEN --with_nms True --type speed
```

### Testing with LWEN
1. The pretrained model is already put in `$ROOT/LWEN/data/Trained_LWEN.pth`.
2. Obtain contour information via CIEN:
```shell
cd $ROOT/CIEN
python test.py --config_file default_CIEN --dataset LISAP_test --with_nms True
```
Then the results can be found in `$ROOT/CIEN/data/result/default_CIEN`.
3. Testing using GT:
```shell
cd $ROOT/LWEN
python GT_test.py --config_file default_LWEN --dataset LISAP_test --checkpoint data/default_LWEN.pth
```
4. Testing using results generated by CIEN:
```shell
python SEG_test.py --config_file default_LWEN --dataset LISAP_test --checkpoint data/default_LWEN.pth --seg_results $ROOT/CIEN/data/result/default_CIEN/py_results_with_ID_and_Weight.jsson
```

## Training

---
### Training with multiple gpus
```shell
cd $ROOT/CIEN(or LWEN)
CUDA_VISIBLE_DEVICES=${gpu_ids} python -m torch.distributed.launch \
--nproc_per_node ${gpu_nums} \
train_net_ddp.py \
--config_file ${dataset} \
--bs ${bs_per_gpu} \
--gpus ${gpu_nums}
```
For example:
```shell
#training LWEN using 4 gpus
cd $ROOT/LWEN
CUDA_VISIBLE_DEVICES=0,1,2,3 python -m torch.distributed.launch \
--nproc_per_node 4 \
train_net_ddp.py \
--config_file default_LWEN \
--bs 32 \
--gpus 4
```

## Acknowledgement

---
The `CIEN` is based on the improvement of [E2EC](https://github.com/zhang-tao-whu/e2ec). Thanks for their amazing works!