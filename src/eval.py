# Author: Bichen Wu (bichen@berkeley.edu) 08/25/2016

"""Evaluation"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import cv2
from datetime import datetime
import os.path
import sys
import time

import numpy as np
from six.moves import xrange
import tensorflow as tf

from config import *
from dataset import pascal_voc, kitti, ball
from utils.util import bbox_transform, Timer
from nets import *

FLAGS = tf.app.flags.FLAGS

# tf.app.flags.DEFINE_string('dataset', 'KITTI', """Currently support PASCAL_VOC or KITTI dataset.""")
tf.app.flags.DEFINE_string('dataset', 'BALL',""" """)
tf.app.flags.DEFINE_string('data_path', 'D:\\Humanoid\\squeezeDet\\squeezeDet-master\\data\\val\\', """Root directory of data""")

tf.app.flags.DEFINE_string('image_set', 'val',                          
                           """Can be train, trainval, val, or test""")

tf.app.flags.DEFINE_string('eval_dir', 'logs\\squeezeDet\\val',
                            """Directory where to write event logs """)

tf.app.flags.DEFINE_string('checkpoint_path', '.\\logs\\squeezeDet\\train',#'/tmp/bichen/logs/squeezeDet/train',
                            """Path to the training checkpoint.""")
tf.app.flags.DEFINE_integer('eval_interval_secs', 60 * 1,
                             """How often to check if new cpt is saved.""")
tf.app.flags.DEFINE_boolean('run_once', False,
                             """Whether to run eval only once.""")
tf.app.flags.DEFINE_string('net', 'squeezeDet',
                           """Neural net architecture.""")
tf.app.flags.DEFINE_string('gpu', '0', """gpu id.""")


def eval_once(saver, ckpt_path, summary_writer, eval_summary_ops, eval_summary_phs, imdb, model):

  with tf.Session(config=tf.ConfigProto(allow_soft_placement=True)) as sess:

    # Restores from checkpoint
    saver.restore(sess, ckpt_path)
    # Assuming model_checkpoint_path looks something like:
    #   /ckpt_dir/model.ckpt-0,
    # extract global_step from it.
    global_step = ckpt_path.split('/')[-1].split('-')[-1]

    num_images = len(imdb.image_idx)

    all_boxes = [[[] for _ in xrange(num_images)]
                 for _ in xrange(imdb.num_classes)]

    _t = {'im_detect': Timer(), 'im_read': Timer(), 'misc': Timer()}

    num_detection = 0.0
    for i in xrange(num_images):
      _t['im_read'].tic()
      images, scales = imdb.read_image_batch(shuffle=False)
      _t['im_read'].toc()

      _t['im_detect'].tic()
      det_boxes, det_probs, det_class = sess.run(
          [model.det_boxes, model.det_probs, model.det_class],
          feed_dict={model.image_input:images})
      _t['im_detect'].toc()

      _t['misc'].tic()
      for j in range(len(det_boxes)): # batch
        # rescale
        det_boxes[j, :, 0::2] /= scales[j][0]
        det_boxes[j, :, 1::2] /= scales[j][1]

        det_bbox, score, det_class = model.filter_prediction(
            det_boxes[j], det_probs[j], det_class[j])

        num_detection += len(det_bbox)
        for c, b, s in zip(det_class, det_bbox, score):
          all_boxes[c][i].append(bbox_transform(b) + [s])
      _t['misc'].toc()

      print ('im_detect: {:d}/{:d} im_read: {:.3f}s '
             'detect: {:.3f}s misc: {:.3f}s'.format(
                i+1, num_images, _t['im_read'].average_time,
                _t['im_detect'].average_time, _t['misc'].average_time))

    print ('Evaluating detections...')
    aps, ap_names = imdb.evaluate_detections(
        FLAGS.eval_dir, global_step, all_boxes)

    print ('Evaluation summary:')
    print ('  Average number of detections per image: {}:'.format(
      num_detection/num_images))
    print ('  Timing:')
    print ('    im_read: {:.3f}s detect: {:.3f}s misc: {:.3f}s'.format(
      _t['im_read'].average_time, _t['im_detect'].average_time,
      _t['misc'].average_time))
    print ('  Average precisions:')

    feed_dict = {}
    for cls, ap in zip(ap_names, aps):
      feed_dict[eval_summary_phs['APs/'+cls]] = ap
      print ('    {}: {:.3f}'.format(cls,ap))

    print ('    Mean average precision: {:.3f}'.format(np.mean(aps)))
    feed_dict[eval_summary_phs['APs/mAP']] = np.mean(aps)
    feed_dict[eval_summary_phs['timing/im_detect']] = \
        _t['im_detect'].average_time
    feed_dict[eval_summary_phs['timing/im_read']] = \
        _t['im_read'].average_time
    feed_dict[eval_summary_phs['timing/post_proc']] = \
        _t['misc'].average_time
    feed_dict[eval_summary_phs['num_det_per_image']] = \
        num_detection/num_images

    print ('Analyzing detections...')
    stats, ims = imdb.do_detection_analysis_in_eval(
        FLAGS.eval_dir, global_step)

    eval_summary_str = sess.run(eval_summary_ops, feed_dict=feed_dict)
    for sum_str in eval_summary_str:
      summary_writer.add_summary(sum_str, global_step)

def evaluate():
  """Evaluate."""  

  os.environ['CUDA_VISIBLE_DEVICES'] = FLAGS.gpu

  with tf.Graph().as_default() as g:

    if FLAGS.net == 'squeezeDet':
      mc = ball_config()
      mc.BATCH_SIZE = 1 # TODO(bichen): allow batch size > 1
      mc.LOAD_PRETRAINED_MODEL = False
      model = SqueezeDet(mc)
    elif FLAGS.net == 'squeezeDet+':
      mc = ball_config()
      mc.BATCH_SIZE = 1 # TODO(bichen): allow batch size > 1
      mc.LOAD_PRETRAINED_MODEL = False
      model = SqueezeDetPlus(mc)

    imdb = ball(FLAGS.image_set, FLAGS.data_path, mc)

    # add summary ops and placeholders
    ap_names = []
    # for cls in imdb.classes:
      # ap_names.append(cls+'_easy')
      # ap_names.append(cls+'_medium')
      # ap_names.append(cls+'_hard')

    eval_summary_ops = []
    eval_summary_phs = {}
    # for ap_name in ap_names:
    ph = tf.placeholder(tf.float32)
    eval_summary_phs['APs'] = ph
    eval_summary_ops.append(tf.summary.scalar('APs', ph))

    ph = tf.placeholder(tf.float32)
    eval_summary_phs['APs/mAP'] = ph
    eval_summary_ops.append(tf.summary.scalar('APs/mAP', ph))

    ph = tf.placeholder(tf.float32)
    eval_summary_phs['timing/im_detect'] = ph
    eval_summary_ops.append(tf.summary.scalar('timing/im_detect', ph))

    ph = tf.placeholder(tf.float32)
    eval_summary_phs['timing/im_read'] = ph
    eval_summary_ops.append(tf.summary.scalar('timing/im_read', ph))

    ph = tf.placeholder(tf.float32)
    eval_summary_phs['timing/post_proc'] = ph
    eval_summary_ops.append(tf.summary.scalar('timing/post_proc', ph))

    ph = tf.placeholder(tf.float32)
    eval_summary_phs['num_det_per_image'] = ph
    eval_summary_ops.append(tf.summary.scalar('num_det_per_image', ph))

    saver = tf.train.Saver(model.model_params)

    summary_writer = tf.summary.FileWriter(FLAGS.eval_dir, g)
    
    ckpts = set() 
    while True:
      if FLAGS.run_once:
        # When run_once is true, checkpoint_path should point to the exact
        # checkpoint file.
        eval_once(
            saver, FLAGS.checkpoint_path, summary_writer, eval_summary_ops,
            eval_summary_phs, imdb, model)
        return
      else:
        # When run_once is false, checkpoint_path should point to the directory
        # that stores checkpoint files.
        ckpt = tf.train.get_checkpoint_state(FLAGS.checkpoint_path)
        if ckpt and ckpt.model_checkpoint_path:
          if ckpt.model_checkpoint_path in ckpts:
            # Do not evaluate on the same checkpoint
            # print ('Wait {:d}s for new checkpoints to be saved ... '
            #           .format(FLAGS.eval_interval_secs))
            # time.sleep(FLAGS.eval_interval_secs)
            break
          else:
            ckpts.add(ckpt.model_checkpoint_path)
            print ('Evaluating {}...'.format(ckpt.model_checkpoint_path))
            eval_once(
                saver, ckpt.model_checkpoint_path, summary_writer,
                eval_summary_ops, eval_summary_phs, imdb, model)
        else:
          print('No checkpoint file found')
          if not FLAGS.run_once:
            print ('Wait {:d}s for new checkpoints to be saved ... '
                      .format(FLAGS.eval_interval_secs))
            time.sleep(FLAGS.eval_interval_secs)


def main(argv=None):  # pylint: disable=unused-argument
  if tf.gfile.Exists(FLAGS.eval_dir):
    tf.gfile.DeleteRecursively(FLAGS.eval_dir)
  tf.gfile.MakeDirs(FLAGS.eval_dir)
  evaluate()


if __name__ == '__main__':
  tf.app.run()
