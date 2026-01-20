from django import forms
from django.forms import ModelForm
from .models import Applicant, ScreeningForm, ProgramChoice
from accounts.models import User, Faculty, Department
from accounts.state import NIGERIA_STATES_AND_LGAS
from datetime import datetime   

class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

class ApplicantForm(ModelForm):
    user = UserForm()
    class Meta:
        model = Applicant
        fields = ['user', 'state', 'phone_number', 'programs', 'mode']

class ApplicantScreeningForm(ModelForm):
    sex = forms.ChoiceField(
        choices=[('M', 'Male'), ('F', 'Female')],
        required=True,
        widget=forms.Select(attrs={'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    state_of_origin = forms.ChoiceField(
        choices=[(state, state) for state in NIGERIA_STATES_AND_LGAS.keys()],
        required=True,
        widget=forms.Select(attrs={'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    local_government = forms.ChoiceField(
        choices=[],  # Initially empty, populated dynamically
        required=True,
        widget=forms.Select(attrs={'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )

    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    middle_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    surname = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
        required=True
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    contact_address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 3}),
        required=True
    )    
    jamb_reg_no = forms.CharField(
        max_length=11,
        required=True,
        widget=forms.TextInput(attrs={'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    jamb_score = forms.CharField(
        max_length=3,
        required=True,
        widget=forms.TextInput(attrs={'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    
    first_choice = forms.ModelChoiceField(
        queryset=None,  # Will be set dynamically
        required=True,
        widget=forms.Select(attrs={'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    second_choice = forms.ModelChoiceField(
        queryset=None,  # Will be set dynamically
        required=False,
        widget=forms.Select(attrs={'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    third_choice = forms.ModelChoiceField(
        queryset=None,  # Will be set dynamically
        required=True,
        widget=forms.Select(attrs={'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    waec_result = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    jamb_result_slip = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    birth_certificate = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    passport_photo = forms.FileField(
        required=True, 
        widget=forms.FileInput(attrs={'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    declaration = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'})
    )
    
    def __init__(self, *args, **kwargs):
        applicant = kwargs.pop('applicant', None)
        super().__init__(*args, **kwargs)
        
        # Populate LGA choices based on the selected state
        if 'state_of_origin' in self.data:
            state = self.data.get('state_of_origin')
            if state in NIGERIA_STATES_AND_LGAS:
                self.fields['local_government'].choices = [(lga, lga) for lga in NIGERIA_STATES_AND_LGAS[state]]
        elif self.instance and self.instance.state_of_origin:
            state = self.instance.state_of_origin
            if state in NIGERIA_STATES_AND_LGAS:
                self.fields['local_government'].choices = [(lga, lga) for lga in NIGERIA_STATES_AND_LGAS[state]]
        
        # Set dynamic program choices based on applicant's program type
        if applicant:
            program_type = applicant.programs.program_type
            choices_queryset = ProgramChoice.objects.filter(
                program_type=program_type,
                is_active=True
            )
            
            self.fields['first_choice'].queryset = choices_queryset
            self.fields['second_choice'].queryset = choices_queryset
            self.fields['third_choice'].queryset = choices_queryset
        else:
            # Default empty queryset if no applicant provided
            empty_queryset = ProgramChoice.objects.none()
            self.fields['first_choice'].queryset = empty_queryset
            self.fields['second_choice'].queryset = empty_queryset
            self.fields['third_choice'].queryset = empty_queryset

    def clean(self):
        cleaned_data = super().clean()
        state = cleaned_data.get('state_of_origin')
        lga = cleaned_data.get('local_government')

        # Validate LGA belongs to the selected state
        if state and lga:
            if state in NIGERIA_STATES_AND_LGAS:
                if lga not in NIGERIA_STATES_AND_LGAS[state]:
                    self.add_error('local_government', 'Invalid LGA for the selected state.')

        # Validate course choices are unique
        first_choice = cleaned_data.get('first_choice')
        second_choice = cleaned_data.get('second_choice')
        third_choice = cleaned_data.get('third_choice')

        choices = [first_choice, second_choice, third_choice]
        choices = [c for c in choices if c is not None]  # Remove None values
        if len(set(choices)) != len(choices):
            self.add_error(None, 'Course choices must be different.')

        return cleaned_data

    class Meta:
        model = ScreeningForm
        fields = '__all__'
        exclude = ['applicant', 'created_at' 'courses']