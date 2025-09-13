import { NgModule } from "@angular/core";
import { CommonModule } from "@angular/common";
import { RouterModule } from "@angular/router";
import { NavbarComponent } from "./navbar.component";
import { BarChart3, LucideAngularModule } from "lucide-angular";

@NgModule({
  imports: [RouterModule, CommonModule, LucideAngularModule.pick({ BarChart3,  })],
  declarations: [NavbarComponent],
  exports: [NavbarComponent],
})
export class NavbarModule {}
