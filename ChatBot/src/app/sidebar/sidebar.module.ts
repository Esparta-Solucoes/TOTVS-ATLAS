import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SidebarComponent } from './sidebar.component';
import { Activity, Database, Edit3, LucideAngularModule, Plus, Settings } from 'lucide-angular';

@NgModule({
    imports: [ RouterModule, CommonModule, LucideAngularModule.pick({ Activity, Settings, Plus, Edit3, Database}) ],
    declarations: [ SidebarComponent ],
    exports: [ SidebarComponent ]
})

export class SidebarModule {}
