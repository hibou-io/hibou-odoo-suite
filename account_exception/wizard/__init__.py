<?xml version="1.0" encoding="UTF-8" ?>
<odoo>

    <record id="view_stock_exception_confirm" model="ir.ui.view">
        <field name="name">Stock Exceptions Rules</field>
        <field name="model">stock.exception.confirm</field>
        <field name="inherit_id" ref="base_exception.view_exception_rule_confirm"/>
        <field name="mode">primary</field>
        <field name="arch" type="xml">
            <xpath expr="//footer" position="inside">
                <button class="oe_link" special="cancel" string="Cancel"/>
            </xpath>
        </field>
    </record>

    <record id="action_invoice_exception_confirm" model="ir.actions.act_window">
        <field name="name">Blocked due to exceptions</field>
        <field name="type">ir.actions.act_window</field>
        <field name="res_model">invoice.exception.confirm</field>
        <field name="view_mode">form</field>
        <field name="view_id" ref="view_invoice_exception_confirm"/>
        <field name="target">new</field>
    </record>

</odoo>
