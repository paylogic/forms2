"""Test AccessFilter forms extension."""
import pytest

from django import forms

from forms2 import FieldAccess, FieldAccessMixin
from tests import record


def access_bank_details(user, instance):
    if user.edit_bank_account:
        if user.edit_contract_id:
            return FieldAccess.enabled
        return FieldAccess.readonly
    return FieldAccess.excluded


def access_contract_id(user, instance):
    if not (user.edit_contract_id and user.do_stuff):
        return FieldAccess.readonly
    return FieldAccess.enabled


def access_check(user, instance):
    return FieldAccess.readonly


@pytest.fixture
def test_model_class():
    from django.db import models

    class TestModel(models.Model):
        pass
    return TestModel


@pytest.fixture
def bank_form_class(test_model_class):
    class BankForm(FieldAccessMixin, forms.ModelForm):

        class Meta:
            model = test_model_class
            access = {
                ('bank_account', 'bank_name', 'bank_balance'): access_bank_details,
                'contract_id': access_contract_id,
                None: access_check,
            }

        bank_account = forms.CharField()
        bank_name = forms.CharField()
        bank_balance = forms.FloatField()
        contract_id = forms.IntegerField()
        some_other_field = forms.CharField()
    return BankForm


User = record('edit_bank_account', 'edit_contract_id', 'do_stuff')


@pytest.fixture
def anon_user():
    """Create test anonymous user (without any permissions)."""
    return User(edit_bank_account=False, edit_contract_id=False, do_stuff=False)


@pytest.fixture
def admin_user():
    """Create test admin user (with all)."""
    return User(edit_bank_account=True, edit_contract_id=True, do_stuff=True)


def test_access_meta(anon_user, admin_user, bank_form_class):
    """Test AccessMixing with Meta declaration."""
    form = bank_form_class(user=anon_user)
    assert form.fields == dict(contract_id=form.fields['contract_id'], some_other_field=form.fields['some_other_field'])
    assert 'readonly' in form.fields['contract_id'].widget.attrs

    form = bank_form_class(user=admin_user)
    assert list(form.fields.keys()) == ['bank_account', 'bank_name', 'bank_balance', 'contract_id', 'some_other_field']
