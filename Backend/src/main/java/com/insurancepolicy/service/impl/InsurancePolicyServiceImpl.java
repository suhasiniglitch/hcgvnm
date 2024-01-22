package com.insurancepolicy.service.impl;

import java.util.List;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.insurancepolicy.dto.InsurancePolicyDTO;
import com.insurancepolicy.service.InsurancePolicyService;

@Service
public class InsurancePolicyServiceImpl implements InsurancePolicyService {

	@Override
	public List<InsurancePolicyDTO> getAllPolicies() {
		// write your logic here
		return null;
	}

	@Override
	public InsurancePolicyDTO getInsurancePolicyById(Long id) {
		// write your logic here
		return null;
	}

	@Override
	@Transactional
	public InsurancePolicyDTO createInsurancePolicy(InsurancePolicyDTO insurancePolicyDTO) {
		// write your logic here
		return null;
	}

	@Override
	@Transactional
	public InsurancePolicyDTO updateInsurancePolicy(Long id, InsurancePolicyDTO insurancePolicyDTO) {
		// write your logic here
		return null;
	}

	@Override
	@Transactional
	public boolean deleteInsurancePolicy(Long id) {
		// write your logic here
		return false;
	}
}
