import os
from typing import Optional
import pytest
import datajoint as dj
from pharus.interface import _DJConnector as DJC
from . import get_schema_as_vm, get_db_creds


@pytest.fixture
def iub_lulab_devo_model_labeledvideo_file(connection: dj.Connection) -> Optional[dj.Table]:
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv('DJ_SUPPORT_FILEPATH_MANAGEMENT', 'TRUE')
        vm = get_schema_as_vm('iub-lulab_devo_model', connection)
        yield None if vm is None else vm.LabeledVideo.File


class TestDJConnector:

    def test_can_init(self):
        djc = DJC()
        assert djc is not None

    @pytest.mark.skipif(
        (get_schema_as_vm('iub-lulab_devo_model', dj.conn(**get_db_creds())) is None),
        reason="Cannot access schema 'iub_lulab_devo_model' with these credentials"
    )
    def test_can_fetch_filepath_attrs(self, iub_lulab_devo_model_labeledvideo_file: dj.Table, connection):
        """
        Tests _DJConnector._fetch_records for a table with a filepath attribute

        https://datajoint.atlassian.net/browse/PLAT-341
        """
        table = iub_lulab_devo_model_labeledvideo_file
        vm = get_schema_as_vm('iub-lulab_devo_model', connection)
        breakpoint()
        assert os.environ.get('DJ_SUPPORT_FILEPATH_MANAGEMENT').upper() == 'TRUE'
        assert table.fetch(as_dict=True, limit=1)
        # assert dj.list_schemas(connection=connection)

