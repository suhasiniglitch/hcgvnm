import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { InsurancePolicy } from '../models/insurance-policy-management.model';

@Injectable({
  providedIn: 'root'
})
export class InsurancePolicyService {
  private apiUrl = '';

  constructor(private http: HttpClient) { }

  getAllPolicies(): any {
    // write your logic here
    return null;
  }

  getPolicyById(id: number): any {
    // write your logic here
    return null;
  }

  createPolicy(policy: InsurancePolicy): any {
    // write your logic here
    return null;
  }

  updatePolicy(id: number, policy: InsurancePolicy): any {
    // write your logic here
    return null;
  }

  deletePolicy(id: number): any {
    // write your logic here
    return null;
  }
}
