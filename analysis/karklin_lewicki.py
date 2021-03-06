import numpy as np
import tensorflow as tf
import matplotlib
import utils.plot_functions as pf
from analysis.base_analysis import Analyzer

class karklin_lewicki(Analyzer):
  def __init__(self, params):
    Analyzer.__init__(self, params)

  def load_params(self, params):
    Analyzer.load_params(self, params)
    self.eval_inference = params["eval_inference"]
    self.eval_density_weights = params["eval_density_weights"]

  """
  plot loss values during learning
  """
  def plot_stats(self, stats):
    losses = {
     "batch_step":stats["batch_step"],
     "recon_loss":stats["recon_loss"],
     "sparse_loss":stats["sparse_loss"],
     "feedback_loss":stats["feedback_loss"],
     "total_loss":stats["total_loss"]}
    loss_filename = self.out_dir+"losses_v"+self.version+self.file_ext
    pf.save_losses(data=losses, labels=None, out_filename=loss_filename)

  """
  plot activity triggered averages
  """
  def plot_ata(self, data, datatype):
    fig_title = "Activity triggered averages on "+datatype+" data"
    for layer_idx, layer in enumerate(data):
      ata_filename = (self.out_dir+"act_trig_avg_layer_"+str(layer_idx)+"_"
        +datatype+"_v"+self.version+self.file_ext)
      ata = layer.reshape(layer.shape[0], int(np.sqrt(
        layer.shape[1])), int(np.sqrt(layer.shape[1])))
      pf.save_data_tiled(ata, normalize=True, title=fig_title,
        save_filename=ata_filename, vmin=-1.0, vmax=1.0)

  """
  Evaluate model and return activations & weights
  Outputs:
    dictionary containing:
      a
      b
      u
      v
      x_
      sigma
      pSNRdB
      u_t
      v_t
      atas
  Inputs:
    model
    data
    cp_loc
  """
  def evaluate_model(self, model, data, cp_loc):
    images = data.images.T
    feed_dict = model.get_feed_dict(images)
    num_imgs = images.shape[1]
    with tf.Session(graph=model.graph) as tmp_sess:
      tmp_sess.run(model.init_op, feed_dict)
      model.weight_saver.restore(tmp_sess, cp_loc)
      tmp_sess.run([model.clear_u, model.clear_v], feed_dict)
      _, a, b, u, v, x_, sigma, pSNRdB, u_t, v_t = tmp_sess.run(
        [model.do_inference, model.a, model.b, model.u, model.v, model.x_,
        model.sigma, model.pSNRdB, model.u_t, model.v_t], feed_dict)
    act_trig_avgs = [np.zeros((u.shape[0], images.shape[0])),
      np.zeros((v.shape[0], images.shape[0]))]
    for layer_idx, layer in enumerate([u, v]):
      max_neuron = np.max(layer, axis=1)
      for img_idx in range(num_imgs):
        for neuron_idx in range(layer.shape[0]):
          if layer[neuron_idx, img_idx] > 0:
            max_act = max([max_neuron[neuron_idx], 0.0000001])
            weight = u[neuron_idx, img_idx] / max_act
            act_trig_avgs[layer_idx][neuron_idx, :] += (
              weight * images[:, img_idx])
        act_trig_avgs[layer_idx] /= num_imgs
    return {"a":a, "b":b, "u":u, "v":v, "x_":x_, "sigma":sigma, "pSNRdB":pSNRdB,
      "u_t":u_t, "v_t":v_t, "ata":act_trig_avgs}
