import argparse
import importlib

parser = argparse.ArgumentParser()
parser.add_argument("--config_file", default='default_LWEN')
parser.add_argument("--dataset", default='LISAP_test')
parser.add_argument("--seg_results",default='path/to/py_results_with_ID_and_Weight')
parser.add_argument("--seg_mode",default='PY') #PY,IMG,MSK
parser.add_argument('--checkpoint', default='path/to/pth')
parser.add_argument('--process', default='ORIGIN')
args = parser.parse_args()
cfg = importlib.import_module('configs.' + args.config_file)

from network import make_network
from train import make_recorder
from Utils import load_network,make_data_loader
from evaluators import make_evaluator
from tqdm import tqdm
import time
import torch

network = make_network()
cfg.val.dataset = args.dataset
val_loader = make_data_loader(args)
evaluator = make_evaluator(cfg)
recorder = make_recorder(cfg)
epoch = load_network(network, args.checkpoint, resume=cfg.resume)
network = network.cuda()
network.eval()

data_size = len(val_loader)
total_time = 0
for batch in tqdm(val_loader):
    if batch is None:
        continue

    for k in batch:
        batch[k] = batch[k].cuda()

    with torch.no_grad():
        start = time.time()
        predict_weights = network(batch[cfg.input_mode])
        total_time += time.time() - start
        output = {'predict_weights': predict_weights, 'true_weights': batch['weight'], 'catids': batch['cls_id']}
        evaluator.evaluate(output, batch)

print(total_time / data_size, '{} FPS'.format(data_size / total_time))
result, fig_stat = evaluator.summarize()

recorder.record_fig('Seg_test', epoch, fig_stat)