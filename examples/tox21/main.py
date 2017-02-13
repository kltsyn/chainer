#!/usr/bin/env python
import argparse

import chainer
from chainer import iterators as I
from chainer import links as L
from chainer import optimizers as O
from chainer import training
from chainer.training import extensions as E

import acc
import data
import loss
import model as model_
import preprocess


parser = argparse.ArgumentParser(
    description='Multitask Learning with Tox21.')
parser.add_argument('--batchsize', '-b', type=int, default=128)
parser.add_argument('--gpu', '-g', type=int, default=0)
parser.add_argument('--out', '-o', type=str, default='result')
parser.add_argument('--epoch', '-e', type=int, default=10)
args = parser.parse_args()


train, test, val = data.get_tox21()
train_iter = I.SerialIterator(train, args.batchsize)
test_iter = I.SerialIterator(test, args.batchsize, repeat=False, shuffle=False)
val_iter = I.SerialIterator(val, args.batchsize, repeat=False, shuffle=False)

C = len(preprocess.tox21_tasks)
model = model_.Model(C)
classifier = L.Classifier(model,
                          lossfun=loss.multitask_sce,
                          accfun=acc.multitask_acc)
if args.gpu >= 0:
    chainer.cuda.get_device(args.gpu).use()
    classifier.to_gpu()

optimizer = O.Adam()
optimizer.setup(classifier)

updater = training.StandardUpdater(train_iter, optimizer, device=args.gpu)
trainer = training.Trainer(updater, (args.epoch, 'epoch'), out=args.out)

trainer.extend(E.Evaluator(test_iter, classifier, device=args.gpu))
trainer.extend(E.snapshot(), trigger=(args.epoch, 'epoch'))
trainer.extend(E.LogReport())
trainer.extend(E.PrintReport(['epoch, ''main/loss', 'main/accuracy',
                              'validation/main/loss', 'validation/main/accuracy',
                              'elapsed_time']))

trainer.run()