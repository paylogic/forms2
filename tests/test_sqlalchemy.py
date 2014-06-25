"""Test SQLAlchemy form extensions."""
import pytest
import mock

from django import forms

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String
from sqlalchemy import create_engine


import forms2
from forms2 import sqlalchemy
from tests import record


def _deep_instance():
    ret = record('a', 'c')
    ret.a = record('b')
    ret.a.b = 'val4'
    ret.c = record('d')
    ret.c.d = 'val5'
    return ret


@pytest.mark.parametrize(
    ['model', 'result'],
    [
        (record('x', 'y'), dict(x='val1', y='val2')),
        (record('z', 'f'), dict(z='val1', f='val2')),
    ])
def test_model_to_dict(model, result):
    """Test model to dict conversion."""
    assert sqlalchemy.model_to_dict(model(**result), result.keys()) == result


@pytest.mark.parametrize(
    ['instance', 'result'],
    [
        (
            _deep_instance(),
            {
                'a.b': 'val4',
                'c.d': 'val5',
            }
        ),
    ]
)
def test_model_to_dict_deep(instance, result):
    """Test model to dict recursive."""
    assert sqlalchemy.model_to_dict(instance, result.keys()) == result


@pytest.mark.parametrize(
    ['model', 'result'],
    [
        (record('x', 'y'), dict(x='val1', y='val2')),
        (record('z', 'f'), dict(z='val3', f='val3')),
    ])
def test_dict_to_model(model, result):
    """Test dict to model conversion."""
    instance = model(**dict(((key, '') for (key, value) in result.items())))
    sqlalchemy.dict_to_model(instance, result)
    assert instance._asdict() == result


@pytest.mark.parametrize(
    ['instance', 'result'],
    [
        (
            _deep_instance(),
            {
                'a.b': 'val4',
                'c.d': 'val5'
            }
        ),
    ]
)
def test_dict_to_model_deep(instance, result):
    """Test dict to model conversion recursive."""
    sqlalchemy.dict_to_model(instance, result)
    assert sqlalchemy.model_to_dict(instance, result.keys()) == result


@pytest.fixture
def model_class():
    """Create test model class."""
    Base = declarative_base()

    class TestModel(Base):
        __tablename__ = 'test_table'
        id = Column(Integer, primary_key=True)
        name = Column(String)
        fullname = Column(String)
        password = Column(String)

        def save():
            pass

    return TestModel


@pytest.fixture
def model(model_class):
    """Create test model instance."""
    return model_class(id=1)


@pytest.fixture
def model_form_class(model_class):
    """Create test model form class."""
    class TestModelForm(forms2.SAModelForm):
        class Meta:
            model = model_class

    return TestModelForm


@pytest.fixture
def query(model_class, session):
    """Create SQLAlchemy Query for model_class."""
    return session.query(model_class)


@pytest.fixture
def session(request, engine):
    """SQLAlchemy session."""
    session = sessionmaker(bind=engine)()
    return session


@pytest.fixture
def engine(request, model_class):
    """SQLAlchemy engine."""
    engine = create_engine('sqlite:///:memory:')
    model_class.metadata.create_all(engine)
    return engine


def test_model_form(monkeypatch, model_form_class, model_class, model):
    """Test SAModelForm."""
    form = model_form_class(instance=model, data={})
    assert form.is_valid()
    with mock.patch.object(model_class, 'save') as mocked:
        form.save()
    mocked.assert_called_once()


def test_model_form_without_instance(model_form_class, model_class, model):
    """Test SAModelForm without an instance."""
    form = model_form_class(data={})
    assert form.is_valid()
    with mock.patch.object(model_class, 'save') as mocked:
        form.save()
    mocked.assert_called_once()


def test_model_choice_field(query, model, session):
    """Test ModelChoiceField."""
    field = sqlalchemy.ModelChoiceField(query)

    assert field.label_from_instance(model) == repr(model)

    field = sqlalchemy.ModelChoiceField(query, label_from_instance=lambda x: str(x.id))

    assert field.label_from_instance(model) == '1'

    assert field.primary_key.name == 'id'

    assert field.prepare_value(model) == 1

    assert field.to_python(None) is None

    session.add(model)
    session.commit()

    with pytest.raises(forms.ValidationError) as exc:
        field.to_python(-1)
    assert '%(' not in sqlalchemy.force_text(exc.value.message)

    assert field.to_python(1) == model


def test_model_multiple_choice_field(query, model, session):
    """Test ModelMultipleChoiceField."""
    field = sqlalchemy.ModelMultipleChoiceField(query)

    with pytest.raises(forms.ValidationError):
        field.clean(None)

    with pytest.raises(forms.ValidationError):
        field.clean([1])

    session.add(model)
    session.commit()

    assert field.clean([1]) == [model]

    assert field.prepare_value(model) == 1

    assert field.prepare_value([model]) == [1]
