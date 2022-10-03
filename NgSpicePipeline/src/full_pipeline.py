from pipeline import *
import torch
from visualutils import *

def CrossFoldValidationFullPipeline(simulator, simulator_name, train_config, device='cpu'):

    pipeline_simulator = simulator

    rerun_training = train_config['rerun_training'] if 'rerun_training' in train_config else True
    font_size = train_config['font_size'] if 'font_size' in train_config else 12
    model = train_config['model'] if 'model' in train_config else models.Model500GELU
    loss = train_config['loss'] if 'loss' in train_config else torch.nn.L1Loss()
    loss_name = train_config['loss_name'] if 'loss_name' in train_config else 'L1'
    epochs = train_config['epochs'] if 'epochs' in train_config else 100
    subset = train_config['subset'] if 'subset' in train_config else [0.05, 0.1, 0.2, 0.5, 0.9]
    color = train_config['color'] if 'color' in train_config else ['r', 'b', 'c', 'y', 'k']
    check_every = train_config['check_every'] if 'check_every' in train_config else 20
    first_eval = train_config['first_eval'] if 'first_eval' in train_config else 1
    graph = train_config['graph'] if 'graph' in train_config else False
    save_data = train_config['save_data'] if 'save_data' in train_config else True


    assert len(color) == len(subset)

    baseline, test_margins, train_margins, test_loss, train_loss, test_accuracy, \
    _, mean_err, mean_perform_err, mean_baseline_err, mean_baseline_performance_err, mean_err_std, \
    mean_performance_err_std, mean_baseline_err_std, \
    mean_baseline_performance_err_std = CrossFoldValidationPipeline(pipeline_simulator, rerun_training, model, loss,
                                                                    epochs, check_every, subset,
                                                                    generate_new_dataset=False, device=device,
                                                                    first_eval=first_eval)

    margins = [0, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5]

    np.set_printoptions(formatter={'float': lambda x: "{0:0.4f}".format(x)})

    print("FINAL RESULT")
    print("Mean error for each subset and it's std")
    print(mean_err)
    print(mean_err_std)

    print("Mean error for each subset performance metrics and it's std")
    print(mean_perform_err)
    print(mean_performance_err_std)

    print("Mean error for each subset baseline and it's std")
    print(mean_baseline_err)
    print(mean_baseline_err_std)

    print("Mean error for each subset baseline performance metrics and it's std")
    print(mean_baseline_performance_err)
    print(mean_baseline_performance_err_std)

    multi_test_mean_margin, multi_test_upper_bound_margin, multi_test_lower_bound_margin, baseline_test_mean_margin, \
    baseline_test_upper_bound_margin, baseline_test_lower_bound_margin = graph_multiple_margin_with_confidence_cross_fold(
        test_margins,
        margins, subset, baseline, color=color, graph=graph,
        save_path="../out_plot/{}-margin-accuracy.png".format(simulator_name), font_size=font_size)

    multi_accuracy, multi_accuracy_lower_bound, \
    multi_accuracy_upper_bound = plot_multiple_accuracy_with_confidence_cross_fold(test_accuracy, epochs, check_every,
                                                                                   subset, first_eval=first_eval,
                                                                                   color=color, graph=graph,
                                                                                   save_path="../out_plot/{}-accuracy.png".format(simulator_name),
                                                                                   font_size=font_size)

    multi_loss, multi_loss_lower_bounds, multi_loss_upper_bounds = plot_multiple_loss_with_confidence_cross_fold(
        test_loss,
        epochs, subset, loss_name, color=color, graph=graph,
        save_path="../out_plot/{}-loss.png".format(simulator_name), font_size=font_size)

    if save_data:
        save_info_dict = {
            "multi_test_mean_margin": multi_test_mean_margin,
            "multi_test_upper_bound_margin": multi_test_upper_bound_margin,
            "multi_test_lower_bound_margin": multi_test_lower_bound_margin,
            "baseline_test_mean_margin": baseline_test_mean_margin,
            "baseline_test_upper_bound_margin": baseline_test_upper_bound_margin,
            "baseline_test_lower_bound_margin": baseline_test_lower_bound_margin,
            "multi_accuracy": multi_accuracy,
            "multi_accuracy_lower_bound": multi_accuracy_lower_bound,
            "multi_accuracy_upper_bound": multi_accuracy_upper_bound,
            "multi_loss": multi_loss,
            "multi_loss_lower_bounds": multi_loss_lower_bounds,
            "multi_loss_upper_bounds": multi_loss_upper_bounds,
            "mean_err": mean_err,
            "mean_performance_err": mean_perform_err,
            "mean_baseline_err": mean_baseline_err,
            "mean_baseline_performance_err": mean_baseline_performance_err,
            "mean_err_std": mean_err_std,
            "mean_performance_err_std": mean_performance_err_std,
            "mean_baseline_err_std": mean_baseline_err_std,
            "mean_baseline_performance_err_std": mean_baseline_performance_err_std
        }

        save_output_data(save_info_dict, simulator_name)