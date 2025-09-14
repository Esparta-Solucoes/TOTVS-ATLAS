import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FooterComponent } from './footer.component';
import { AlertTriangle, BarChart3, LineChart, LucideAngularModule, Mic, Send, Target } from 'lucide-angular';
import { FormsModule, ReactiveFormsModule } from "@angular/forms";

@NgModule({
    imports: [RouterModule, CommonModule, LucideAngularModule.pick({ Mic, Send, BarChart3, LineChart, Target, AlertTriangle }), FormsModule, ReactiveFormsModule],
    declarations: [ FooterComponent ],
    exports: [ FooterComponent ]
})

export class FooterModule {}
