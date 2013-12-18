forms2: Django forms extra features
===================================

The ``forms2`` package provides an enhanced version of django forms. In particular, the SQLAchemy integration and
a per-field access control.

.. image:: https://api.travis-ci.org/paylogic/forms2.png
   :target: https://travis-ci.org/paylogic/forms2
.. image:: https://pypip.in/v/forms2/badge.png
   :target: https://crate.io/packages/forms2/
.. image:: https://coveralls.io/repos/paylogic/forms2/badge.png?branch=master
   :target: https://coveralls.io/r/paylogic/forms2


Installation
------------

.. sourcecode::

    pip install forms2


Usage
-----

SQLAlchemy model form example:

.. code-block:: python

    class MyModelForm(SAModelForm):
        class Meta:
            model = MyModel
            mapping = {
                'field1': 'instance.child.attribute',
                'field2': 'attribute3',
            }
        field1 = forms.IntegerField()
        field2 = forms.CharField()


A simple example showing field access control:

.. code-block:: python

    class MyForm(Form, FieldAccessMixin):
        class Meta:
            access = {
                ('field1', 'field2'): access_admin,
                'field3': MyForm.access_admin1,
                None: lambda user, instance: FieldAccess.enabled,
            }
        field1 = forms.IntegerField()

        @classmethod
        def access_admin1(cls):
            return FieldAccess.readonly

A more realistic example for field access control:

.. code-block:: python

    def access_bank_details(user, instance):
        if not has_perm(user, instance, 'edit_bank_account'):
            if has_perm(user, instance, 'edit_contract_id'):
                return FieldAccess.readonly
            return FieldAccess.excluded
        return FieldAccess.enabled

    def access_contract_id(user, instance):
        if not (has_perm(user, instance, 'edit_contract_id') and has_perm(user, instance, 'do_stuff')):
                return FieldAccess.readonly

    class BankForm(Form, FieldAccessMixin):
        class Meta:
            access = {
                ('bank_account', 'bank_name', 'bank_balance'): access_bank_details,
                'contract_id': access_contract_id,
                None: BankForm.access_check,
            }

        bank_account = forms.CharField()
        bank_name = forms.CharField()
        bank_balance = forms.FloatField()

        contract_id = forms.IntegerField()

        some_other_field = forms.CharField()

        @classmethod
        def access_check(cls):
            return FieldAccess.readonly

Field access control using filter syntax:

.. code-block:: python

    @access_filter
    def can_view_event(user, instance):
        if user.has_perm('event', 'view'):
            return FieldAccess.enabled

    @access_filter
    def can_view_merchant(user, instance):
        if user.has_perm('merchant', 'view'):
            return FieldAccess.enabled

    @access_filter
    def exclude_for_not_finance(user, instance):
        if not user.has_perm('merchant', 'some_financial_permission'):
            return FieldAccess.excluded

    ...

        access = {
            # Filters are applied left to right, the result is the first filter to return a FieldAccess value

            # This will be enabled if you can view the event, else readonly
            'field_a': can_view_event | default(FieldAccess.readonly),

            # This will be enabled if you can view the event OR the merchant, else excluded
            'field_b': can_view_event | can_view_merchant | default(FieldAccess.excluded),

            # This will be enabled if you can view the event AND the merchant, else excluded
            'field_b2': can_view_event & can_view_merchant | default(FieldAccess.excluded),

            # This will be excluded if you don't have some finance permission, else enabled (this is the default)
            'field_c': exclude_for_not_finance
        }


Contact
-------

If you have questions, bug reports, suggestions, etc. please create an issue on
the `GitHub project page <http://github.com/paylogic/forms2>`_.


License
-------

This software is licensed under the `MIT license <http://en.wikipedia.org/wiki/MIT_License>`_

See `License <https://github.com/paylogic/forms2/blob/master/LICENSE.txt>`_


© 2013 Paylogic International.
