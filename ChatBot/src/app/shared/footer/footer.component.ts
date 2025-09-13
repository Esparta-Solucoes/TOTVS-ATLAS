import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';

declare var $:any;

@Component({
    selector: 'footer-cmp',
    templateUrl: 'footer.component.html',
    styleUrls: ['./footer.component.scss'],
})

export class FooterComponent implements OnInit{
    test : Date = new Date();

    public form: FormGroup;

    constructor(
        private formBuilder: FormBuilder
    ) { }

    ngOnInit() {
        this.createFormulario();
    }

    public createFormulario() {
        this.form = this.formBuilder.group({
            input: [{value: "", disabled: false}, [Validators.required]]
        });
    }

    public enviarMensagem() {
        console.log(this.form.value);
        this.form.reset();
    }
}
