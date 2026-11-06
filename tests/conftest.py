import pytest

import core.db as core_db


@pytest.fixture(autouse=True)
def _isolate_bundle_seed(tmp_path_factory, monkeypatch):
    """
    CARD-PARMA-26: DatabaseManager siembra el compendio desde data/dnd_database.db del
    bundle. En desarrollo ese archivo existe en el repo y tendría compendio real, lo que
    haría que las pruebas dependan del estado local. Aquí el bundle apunta a un
    directorio vacío para que cada prueba parta de una base sin sembrar.
    """
    empty_bundle = tmp_path_factory.mktemp("no_bundle_seed")
    monkeypatch.setattr(core_db, "get_bundle_dir", lambda: str(empty_bundle))
