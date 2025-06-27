from flask_wtf import FlaskForm
from wtforms import FloatField, SubmitField, StringField, FieldList, FormField
from wtforms.validators import DataRequired, NumberRange

class ROICalculatorForm(FlaskForm):
    selling_price = FloatField('Selling Price', validators=[
        DataRequired(),
        NumberRange(min=0, message="Value must be positive")
    ])
    units_sold = FloatField('Units Sold', validators=[
        DataRequired(),
        NumberRange(min=0, message="Value must be positive")
    ])
    cost = FloatField('Campaign Cost', validators=[
        DataRequired(),
        NumberRange(min=0, message="Value must be positive")
    ])
    submit = SubmitField('Calculate ROI')

class CampaignForm(FlaskForm):
    name = StringField('Campaign Name', validators=[DataRequired()])
    roi_percent = FloatField('ROI (%)', validators=[
        DataRequired(),
        NumberRange(min=0, message="ROI must be positive")
    ])
    max_allocation = FloatField('Max Budget', validators=[
        DataRequired(),
        NumberRange(min=0, message="Budget must be positive")
    ])

class BudgetAllocatorForm(FlaskForm):
    total_budget = FloatField('Total Budget', validators=[
        DataRequired(),
        NumberRange(min=0, message="Budget must be positive")
    ])
    campaigns = FieldList(
        FormField(CampaignForm),
        min_entries=1
    )
    submit = SubmitField('Optimize Allocation')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.campaigns:
            self.campaigns.append_entry()  # Ensure at least one campaign exists