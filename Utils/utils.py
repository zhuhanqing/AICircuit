import yaml
import os
from os.path import join
import numpy as np
from torch.cuda import is_available
import shutil


CONFIG_PATH = os.path.join(os.path.join(os.getcwd(), "config"))

DEFAULT_TRAIN_CONFIG_PATH = os.path.join(CONFIG_PATH, "train_config.yaml")
DEFAULT_VISUAL_CONFIG_PATH = os.path.join(CONFIG_PATH, "visual_config.yaml")


def load_yaml(yaml_path):
    with open(yaml_path, "r") as file:
        config_yaml = yaml.safe_load(file)
    return config_yaml


def load_circuit(circuit_name):
    """Load circuit"""
    config_folder = join("config", "circuits")
    folder = join(config_folder, circuit_name)
    print(folder)
    config = load_yaml(folder)

    return config


def load_train_config(configpath=DEFAULT_TRAIN_CONFIG_PATH):

    train_config = load_yaml(configpath)
    if train_config["device"] == "cuda":
        if is_available():
            train_config["device"] = "cuda:0"
        else:
            train_config["device"] = "cpu"

    return train_config


def load_visual_config(configpath=DEFAULT_VISUAL_CONFIG_PATH):
    return load_yaml(configpath)


def parsetxtToDict(file_path):
    with open(file_path, "r") as file:
        file_info = file.readlines()
        return_dict = dict()

        for line in file_info:
            line_info = line.strip().split(":")
            try:
                return_dict[line_info[0]] = float(line_info[1])
            except ValueError:
                return_dict[line_info[0]] = line_info[1]
        return return_dict
    

def generate_metrics_given_config(train_config):

    metrics_dict = dict()
    if train_config["loss_per_epoch"]:
        metrics_dict["train_loss"] = []
        metrics_dict["validation_loss"] = []

    return metrics_dict


def merge_metrics(parent_metrics, child_metrics):

    for k in parent_metrics.keys():
        if k in child_metrics.keys():
            parent_metrics[k].append(child_metrics[k])


def save_result(result, pipeline_save_name, config_path=None):

    save_folder = os.path.join(os.path.join(os.getcwd(), "result_out"), pipeline_save_name)
    os.mkdir(save_folder)
    for k in result.keys():
        out_variable_save_path = os.path.join(save_folder, k + ".npy")
        np.save(out_variable_save_path, result[k])

    if config_path is not None:
        shutil.copyfile(config_path, os.path.join(save_folder, "train_config.yaml"))


def save_numpy(array, save_name, simulator, model_name):
    path = join(simulator.arguments["out"], model_name, save_name)
    np.save(path, array)
    

def saveDictToTxt(dict, save_path):
    with open(save_path, "w") as file:
        count = 0
        for k,v in dict.items():
            if count != 0:
                file.write('\n')
            file.write(str(k) + ":" + str(v))
            count += 1


def sortVector(parameter, performance):

    data = np.hstack((performance, parameter))

    for i in range(len(performance.shape)):
        data = sorted(data, key=lambda x: x[i], reverse=True)
    data = np.array(data)
    return data[:, performance.shape[1]:], data[:, :performance.shape[1]]


def checkAlias(parameter, performance):

    sort_parameter, sort_performance = sortVector(parameter, performance)

    counter = 0
    duplicate_amount = 0
    while counter <= len(sort_performance) - 2:
        if np.all(np.equal(sort_performance[counter], sort_performance[counter + 1])):
            print("BELOW ARE THE DUPLICATE CASE")
            print("THE TWO DIFFERENT PARAMETER")
            print(sort_parameter[counter])
            print(sort_parameter[counter + 1])
            print("THE SAME RESULT PERFORMANCE")
            print(sort_performance[counter])

            duplicate_amount += 1
        counter += 1

    print("TOTAL DUPLICATE CASE IS {}".format(duplicate_amount))
    if duplicate_amount > 0:
        raise ValueError("THERE ARE ALIASING IN THE RESULT")


def generate_train_config_for_single_pipeline(train_config, model_config):

    new_train_config = dict(train_config)

    del new_train_config["circuits"]
    del new_train_config["model_config"]

    if "extra_args" in model_config.keys():
        for k,v in model_config["extra_args"].items():
            new_train_config[k] = v

    return new_train_config


def update_train_config_given_model_type(model_type, train_config):

    train_config["loss_per_epoch"] = True if "loss_per_epoch" not in train_config else train_config["loss_per_epoch"]

    if model_type == 0:
        #Sklearn model, so no loss and accuracy per epochs
        train_config["loss_per_epoch"] = False
    elif model_type == 1:
        #Pytorch model, so have loss per epoch
        train_config["epochs"] = 100 if "epochs" not in train_config else train_config["epochs"]
    else:
        #Lookup model, no loss accuracy and no train margin
        train_config["loss_per_epoch"] = False


def check_comparison_value_diff(train_config, value, key):
    if value is None:
        if key in train_config.keys():
            return train_config[key]
        else:
            return None
    else:
        if key not in train_config.keys() or train_config[key] != value:
            raise ValueError("The {} across different comparison is not the same".format(key))
        else:
            return value


def get_margin_error(y_hat, y, sign):
    """ Get the margin error of the prediction """
    delta = y_hat*sign >= y*sign
    delta = np.where(delta, 0, y_hat - y)
    return np.abs(delta/y)


def get_relative_margin_error(y_hat, y, sign):
    return np.abs((y_hat-y) / y)