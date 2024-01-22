// TypeScript component
import { Component, OnInit } from '@angular/core';
import { InsurancePolicyService } from '../../services/insurance-policy.service';
import { InsurancePolicy } from '../../models/insurance-policy-management.model';

@Component({
  selector: 'app-insurance-policy',
  templateUrl: './insurance-policy-management.component.html',
  styleUrls: ['./insurance-policy-management.component.css']
})
export class InsurancePolicyComponent implements OnInit {
  policies: InsurancePolicy[] = [];
  selectedPolicy: InsurancePolicy = {
    policyId: 0,
    policyNumber: '',
    policyType: '',
    premiumAmount: 0,
    startDate: new Date(),
    endDate: new Date(),
    isActive: false,
    customerId: 0
  };

  constructor(private insurancePolicyService: InsurancePolicyService) { }

  ngOnInit(): void {
    // write your logic here
  }

  loadPolicies(): void {
    // write your logic here
  }

  addPolicy(): void {
    // write your logic here
  }

  showUpdateForm(id: number): void {
    // write your logic here
  }

  updatePolicyApi(): void {
    // write your logic here
  }

  deletePolicy(id: number): void {
    // write your logic here
  }

  selectPolicy(policy: InsurancePolicy): void {
    // write your logic here
  }

  createEmptyPolicy(): InsurancePolicy {
    // write your logic here
    // feel free to update this
    return this.selectedPolicy;
  }
}
