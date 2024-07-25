import csv
import os
import re
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

spectrum_keys = {
    'AcquireNum': 0,
    'CCDCalcuTemp': 1,
    'CCDOriginalTemp': 2,
    'LightSourceCalcuTemp': 3,
    'LightSourceOriginalTemp': 4,
    'ExpTime': 5
}


class ExperimentMaterial:
    def __init__(self,
                 material_name,
                 spectrum_id,
                 expected_ccd_temp,
                 actual_ccd_temp,
                 expected_light_src_temp,
                 actual_light_src_temp,
                 exposure_time,
                 intensity_data):
        self.material_name = material_name
        self.spectrum_id = spectrum_id
        self.expected_ccd_temp = expected_ccd_temp
        self.actual_ccd_temp = actual_ccd_temp
        self.expected_light_src_temp = expected_light_src_temp
        self.actual_light_src_temp = actual_light_src_temp
        self.exposure_time = exposure_time
        self.intensity_data = intensity_data

    @staticmethod
    def extract_chemical_name(experiment_name):
        match = re.search(r'_([^_-]+)-', experiment_name)
        if match:
            # 匹配成功，返回化学物质的名称
            return match.group(1)
        else:
            # 没有找到匹配，返回None
            return None

    @staticmethod
    def plot_experiment(dir_path, file):
        experiment = ExperimentMaterial.read_experiment_data_from(dir_path, file)
        spectrums = []
        for record in experiment:
            intensity = [value for _, value in record.intensity_data]
            int_intensity = [int(item) for item in intensity if item.isdigit()]
            spectrums.append(int_intensity)

        print(f'{file} has {len(spectrums)} record')
        if len(experiment):
            exp_time = experiment[0].exposure_time
        else:
            print(f'{file} is empty!!!')
            return
        ExperimentMaterial.plot_spectrums(spectrums, file_name=f'{exp_time}{file}', save_dir=dir_path)

    @staticmethod
    def plot_dir(dir_path, target_chemical: str = '*', reverse=True):
        files = os.listdir(dir_path)
        files.sort(reverse=reverse)
        for file in files:
            if ExperimentMaterial.extract_chemical_name(file) == target_chemical or target_chemical == '*':
                ExperimentMaterial.plot_experiment(dir_path, file)

    @staticmethod
    def plot_spectrums(spectrums, file_name, save_dir=''):
        fig, ax = plt.subplots()
        for spec in spectrums:
            ax.plot(spec)
        matplotlib.rcParams['font.sans-serif'] = ['Source Han Sans TW', 'Arial Unicode MS']  # 指定使用字体（确保你的系统中有这些字体）
        matplotlib.rcParams['axes.unicode_minus'] = False  # 正确显示负号

        ax.set_title(f'raw data {os.path.splitext(file_name)[0]}')
        ax.set_xlabel('wave number')
        ax.set_ylabel("Intensity")

        # 显示图形
        if save_dir:
            plt.savefig(save_dir + '\\' + os.path.splitext(file_name)[0] + '.png')
            plt.close()
        else:
            plt.show()

    @staticmethod
    def get_material_name_from_file_name(csv_file):
        match = re.search(r'-2024', csv_file)
        if match:
            return csv_file[:match.start()]
        else:
            print("Not a material")
            print("Error from ExperimentalMaterial.py,get_material_name_from_file_name")
            return None

    @staticmethod
    def read_experiment_data_from(csv_dir: str, csv_file: str) -> list['ExperimentMaterial']:
        experiment_materials = []
        with open(csv_dir + '\\' + csv_file, 'r', newline='') as data_file:
            csv_reader = csv.reader(data_file)
            material_name = ExperimentMaterial.get_material_name_from_file_name(csv_file)
            key_list = next(csv_reader)

            for value_list in csv_reader:
                index_intensity = zip(key_list[6:], value_list[6:])
                intensity_data = []
                for k, v in index_intensity:
                    intensity_data.append((k, v))
                exp_material = ExperimentMaterial(material_name=material_name,
                                                  spectrum_id=int(value_list[spectrum_keys['AcquireNum']]),
                                                  expected_ccd_temp=value_list[spectrum_keys['CCDCalcuTemp']],
                                                  actual_ccd_temp=value_list[spectrum_keys['CCDOriginalTemp']],
                                                  expected_light_src_temp=value_list[
                                                      spectrum_keys['LightSourceCalcuTemp']],
                                                  actual_light_src_temp=value_list[
                                                      spectrum_keys['LightSourceOriginalTemp']],
                                                  exposure_time=value_list[spectrum_keys['ExpTime']],
                                                  intensity_data=intensity_data
                                                  )
                experiment_materials.append(exp_material)
        return experiment_materials

    @staticmethod
    def save_experiment_data_to(csv_dir: str, csv_file: str, experiments: list['ExperimentMaterial']) -> None:
        # 构建完整的文件路径
        full_path = os.path.join(csv_dir, csv_file)

        # 检查实验列表是否为空
        if not experiments:
            print("No experiment data provided.")
            return
        print(f'writing {len(experiments)} records into{full_path}')
        # 打开文件准备写入
        with open(full_path, mode='w', newline='') as file:
            writer = csv.writer(file)

            # 获取intensity_data中的所有可能的键（假设所有实验中的键是相同的）
            intensity_keys = [key for key, _ in experiments[0].intensity_data]

            # 构建CSV的头部
            headers = [
                          'AcquireNum', 'CCDCalcuTemp', 'CCDOriginalTemp',
                          'LightSourceCalcuTemp', 'LightSourceOriginalTemp',
                          'ExpTime'
                      ] + intensity_keys  # 添加intensity_data的键
            writer.writerow(headers)

            # 遍历所有实验，写入它们的数据
            for exp in experiments:
                # 构建基本数据行
                row = [
                    exp.spectrum_id, exp.expected_ccd_temp, exp.actual_ccd_temp,
                    exp.expected_light_src_temp, exp.actual_light_src_temp,
                    exp.exposure_time
                ]

                # 添加intensity_data，确保顺序与头部匹配
                intensity_dict = dict(exp.intensity_data)
                intensity_values = [intensity_dict.get(key, '') for key in intensity_keys]
                row.extend(intensity_values)

                # 写入行数据
                writer.writerow(row)

    @staticmethod
    def filter_experiment(experiment2filter: list['ExperimentMaterial'], target: list['ExperimentMaterial']):
        assert len(experiment2filter) >= len(target), 'Target should have less element to remove bad record of others'
        filtered = [suspicious for suspicious in experiment2filter for clean in target
                    if suspicious.spectrum_id == clean.spectrum_id]
        return filtered
