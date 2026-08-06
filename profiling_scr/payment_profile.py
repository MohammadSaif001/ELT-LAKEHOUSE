import pandas as pd
from spark.common.logger import get_logger
from profiling_scr.common import load_csv, save_profile

logger = get_logger(__name__)

def build_payment_profiles() -> None:
    
    """
    Build payment profiling metadata from the original Olist datasets.
    
        Generates:
            - payment_type_distribution.json
            - payment_installments_distribution.json
            - payment_value_stats.json
            - payment_sequence_stats.json
            - payment_sequential_distribution.json
        """
        
    payment = load_csv("olist_order_payments_dataset.csv")
    payment.columns = payment.columns.str.strip().str.strip('"')
    
    #===========================
    # Payment Type Distribution
    #===========================
    payment_type_distribution = (
    payment["payment_type"]
    .str.strip()
    .value_counts(normalize=True)
    .round(4)
    .to_dict()
    )
    save_profile(
        payment_type_distribution,
        "payment_type_distribution.json",
    )
    logger.info("Generated payment type distribution")
    
    #==================================
    # Payment Installments Distribution
    #==================================
    
    payment_installment = (
    payment["payment_installments"]
    .value_counts(normalize=True)
    .sort_index()
    .round(6)
    .to_dict()
    )
    save_profile(
        payment_installment,
        "payment_installments_distribution.json",
    )
    logger.info("Generated payment installments distribution")
    
    #===========================
    # Payment Value Stats
    #===========================
    payment_value = (
    payment["payment_value"]
    .describe()
    .to_dict()
    )

    save_profile(
        payment_value,
        "payment_value_stats.json",
    )
    logger.info("Generated payment value stats")
    
    #===========================================
    # Payment sequence stats and distribution
    #===========================================
    payment_sequence_stats = (
    payment["payment_sequential"]
    .describe()
    .to_dict()
    )
    
    save_profile(
        payment_sequence_stats,
        "payment_sequence_stats.json",
    )
    payment_sequential = (
    payment["payment_sequential"]
    .value_counts(normalize=True)
    .sort_index()
    .round(6)
    .to_dict()
        )
    
    save_profile(
        payment_sequential,
        "payment_sequential_distribution.json",
    )
    logger.info("Generated payment sequence stats and distribution")