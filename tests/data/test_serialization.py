# Copyright The PyTorch Lightning team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import pytest
import torch
from pytorch_lightning import Trainer
from pytorch_lightning.callbacks import ModelCheckpoint
from torch.utils.data.dataloader import DataLoader

from flash.core import Task
from flash.data.data_pipeline import DataPipeline
from flash.data.process import Preprocess


class CustomModel(Task):

    def __init__(self):
        super().__init__(model=torch.nn.Linear(1, 1), loss_fn=torch.nn.MSELoss())


class CustomPreprocess(Preprocess):

    @classmethod
    def load_data(cls, data):
        return data


@pytest.mark.skipif(reason="Still using DataPipeline Old API")
def test_serialization_data_pipeline(tmpdir):
    model = CustomModel()

    checkpoint_file = os.path.join(tmpdir, 'tmp.ckpt')
    checkpoint = ModelCheckpoint(tmpdir, 'test.ckpt')
    trainer = Trainer(callbacks=[checkpoint], max_epochs=1)
    dummy_data = DataLoader(list(zip(torch.arange(10, dtype=torch.float), torch.arange(10, dtype=torch.float))))
    trainer.fit(model, dummy_data)

    assert model.data_pipeline is None
    trainer.save_checkpoint(checkpoint_file)

    loaded_model = CustomModel.load_from_checkpoint(checkpoint_file)
    assert loaded_model.data_pipeline is None

    model.data_pipeline = DataPipeline(CustomPreprocess())

    trainer.fit(model, dummy_data)
    assert model.data_pipeline
    assert isinstance(model.preprocess, CustomPreprocess)
    trainer.save_checkpoint(checkpoint_file)
    loaded_model = CustomModel.load_from_checkpoint(checkpoint_file)
    assert loaded_model.data_pipeline
    assert isinstance(loaded_model.preprocess, CustomPreprocess)
    for file in os.listdir(tmpdir):
        if file.endswith('.ckpt'):
            os.remove(os.path.join(tmpdir, file))