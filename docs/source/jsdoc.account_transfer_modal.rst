jsdoc.account\_transfer\_modal
==============================

File: ``biweeklybudget/flaskapp/static/js/account_transfer_modal.js``

.. js:function:: accountTransferDivForm()

   Generate the HTML for the form on the Modal

   

   

.. js:function:: accountTransferModal(txfr_date)

   Show the modal popup for transferring between accounts.
   Uses :js:func:`accountTransferDivForm` to generate the form.

   :param string txfr_date: The date, as a "yyyy-mm-dd" string, to default the form to. If null or undefined, will default to ``BIWEEKLYBUDGET_DEFAULT_DATE``.
   

   

