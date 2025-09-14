import { NgModule } from "@angular/core";
import { CommonModule } from "@angular/common";
import { RouterModule } from "@angular/router";
import { NavbarComponent } from "./navbar.component";
import { BarChart3, ExternalLink, LucideAngularModule, Settings, Shield, Zap } from "lucide-angular";

@NgModule({
  imports: [RouterModule, CommonModule, LucideAngularModule.pick({ BarChart3, Zap, Shield, ExternalLink, Settings})],
  declarations: [NavbarComponent],
  exports: [NavbarComponent],
})
export class NavbarModule {}
